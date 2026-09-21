from concurrent.futures import ThreadPoolExecutor
import hashlib
import hmac
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import app as bot_app
import config
import payments
from telegram_api import TelegramAPIError


class StripePaymentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        settings = dict(STRIPE_SECRET_KEY="sk_test_dummy", STRIPE_WEBHOOK_SECRET="whsec_dummy",
                        WEBHOOK_SECRET_TOKEN="telegram-secret", CHANNEL_CHAT_ID="-10042",
                        PUBLIC_BASE_URL="https://example.com", SUBSCRIPTION_PRICE_PENCE=100,
                        SUBSCRIPTION_CURRENCY="GBP", SUBSCRIPTION_DURATION_DAYS=365,
                        PAYMENTS_DB=Path(self.tmp.name) / "payments.sqlite3")
        for name, value in settings.items():
            p = patch.object(config, name, value)
            p.start()
            self.addCleanup(p.stop)
        self.client = bot_app.app.test_client()
        self.session = dict(id="cs_test_42", payment_status="paid", mode="payment",
                            amount_total=100, currency="gbp", client_reference_id="42",
                            metadata={"telegram_user_id": "42", "telegram_chat_id": "-10042"})
        self.create = patch.object(payments.stripe.checkout.Session, "create", return_value=SimpleNamespace(
            id="cs_test_42", url="https://checkout.stripe.com/test", expires_at=int(time.time()) + 3600))
        self.create_mock = self.create.start()
        self.addCleanup(self.create.stop)
        payments.checkout_url(42, -10042)
        self.member = patch.object(payments, "get_chat_member", return_value={"status": "left"})
        self.member.start()
        self.addCleanup(self.member.stop)
        self.approval = patch.object(payments, "approve_chat_join_request")
        self.approve_mock = self.approval.start()
        self.addCleanup(self.approval.stop)

    def webhook(self, session=None, event_type="checkout.session.completed", secret=None):
        body = json.dumps({"id": "evt_test", "object": "event", "type": event_type,
                           "data": {"object": session or self.session}})
        timestamp = int(time.time())
        signature = hmac.new((secret or config.STRIPE_WEBHOOK_SECRET).encode(),
                             f"{timestamp}.{body}".encode(), hashlib.sha256).hexdigest()
        return self.client.post("/stripe/webhook", data=body, content_type="application/json",
                                headers={"Stripe-Signature": f"t={timestamp},v1={signature}"})

    def test_checkout_binds_identity_and_reuses_pending_session(self):
        self.assertEqual(payments.checkout_url(42, -10042), "https://checkout.stripe.com/test")
        self.create_mock.assert_called_once()
        args = self.create_mock.call_args.kwargs
        self.assertEqual(args["metadata"]["telegram_user_id"], "42")
        self.assertEqual(args["line_items"][0]["price_data"]["unit_amount"], 100)

    def test_signed_paid_event_approves_only_once(self):
        self.assertEqual(self.webhook().status_code, 200)
        self.assertEqual(self.webhook().status_code, 200)
        self.approve_mock.assert_called_once_with(-10042, 42)

    def test_concurrent_deliveries_approve_once(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(payments.fulfill, [self.session] * 4))
        self.approve_mock.assert_called_once_with(-10042, 42)

    def test_bad_signature_cannot_grant_access(self):
        self.assertEqual(self.webhook(secret="wrong").status_code, 400)
        self.approve_mock.assert_not_called()

    def test_unpaid_then_delayed_success(self):
        self.assertEqual(self.webhook(dict(self.session, payment_status="unpaid")).status_code, 200)
        self.approve_mock.assert_not_called()
        self.assertEqual(self.webhook(event_type="checkout.session.async_payment_succeeded").status_code, 200)
        self.approve_mock.assert_called_once()

    def test_unknown_checkout_cannot_grant_access(self):
        self.assertEqual(self.webhook(dict(self.session, id="cs_unknown")).status_code, 200)
        self.approve_mock.assert_not_called()

    def test_mismatched_amount_currency_or_identity_cannot_grant_access(self):
        for changes in ({"amount_total": 1}, {"currency": "usd"}, {"client_reference_id": "99"},
                        {"metadata": {"telegram_user_id": "99", "telegram_chat_id": "-10042"}}):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    payments.fulfill(dict(self.session, **changes))
        self.approve_mock.assert_not_called()

    def test_telegram_failure_is_retryable_and_payment_is_preserved(self):
        self.approve_mock.side_effect = TelegramAPIError("approveChatJoinRequest", "temporary failure")
        with self.assertLogs(bot_app.app.logger, level="ERROR"):
            self.assertEqual(self.webhook().status_code, 500)
        with payments.database() as db:
            before = db.execute("SELECT * FROM checkouts").fetchone()
            self.assertIsNotNone(before["paid_until"])
            self.assertEqual(before["fulfilled"], 0)
        self.approve_mock.side_effect = None
        self.assertEqual(self.webhook().status_code, 200)
        with payments.database() as db:
            after = db.execute("SELECT * FROM checkouts").fetchone()
            self.assertEqual(after["paid_until"], before["paid_until"])
            self.assertEqual(after["fulfilled"], 1)

    def test_already_member_is_fulfilled_after_interrupted_delivery(self):
        with patch.object(payments, "get_chat_member", return_value={"status": "member"}):
            self.assertEqual(self.webhook().status_code, 200)
        self.approve_mock.assert_not_called()

    def test_join_request_prompts_and_paid_rejoin_does_not_charge(self):
        join = {"chat": {"id": -10042}, "from": {"id": 42}, "user_chat_id": 4242}
        with patch.object(bot_app, "send_message") as send:
            bot_app.process_update({"chat_join_request": join})
            self.assertEqual(send.call_args.args[0], 4242)
            self.assertIn("checkout.stripe.com", send.call_args.args[1])
            self.approve_mock.assert_not_called()
            self.webhook()
            send.reset_mock()
            bot_app.process_update({"chat_join_request": join})
            send.assert_not_called()
            self.assertEqual(self.create_mock.call_count, 1)

    def test_telegram_webhook_requires_secret(self):
        response = self.client.post("/telegram/webhook", json={})
        self.assertEqual(response.status_code, 403)

    def test_success_page_cannot_grant_access(self):
        self.assertEqual(self.client.get("/payment/success").status_code, 200)
        self.approve_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
