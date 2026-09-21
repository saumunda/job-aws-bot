import sys
import unittest
from pathlib import Path


BOT_DIR = Path(__file__).resolve().parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

import app as bot_app
import config


class ExternalPaymentLinkTests(unittest.TestCase):
    def setUp(self):
        self.original_config = {
            "TELEGRAM_BOT_TOKEN": config.TELEGRAM_BOT_TOKEN,
            "CHANNEL_CHAT_ID": config.CHANNEL_CHAT_ID,
            "PAYMENT_LINK": config.PAYMENT_LINK,
            "SUBSCRIPTION_PRICE_PENCE": config.SUBSCRIPTION_PRICE_PENCE,
            "SUBSCRIPTION_CURRENCY": config.SUBSCRIPTION_CURRENCY,
        }
        self.original_send_message = bot_app.send_message
        self.original_record_prompt = bot_app.storage.record_prompt

        config.TELEGRAM_BOT_TOKEN = "123456:test-token"
        config.CHANNEL_CHAT_ID = "-1001234567890"
        config.PAYMENT_LINK = "https://pay.example/subscription"
        config.SUBSCRIPTION_PRICE_PENCE = 100
        config.SUBSCRIPTION_CURRENCY = "GBP"

    def tearDown(self):
        for name, value in self.original_config.items():
            setattr(config, name, value)
        bot_app.send_message = self.original_send_message
        bot_app.storage.record_prompt = self.original_record_prompt

    def test_validate_config_requires_https_payment_link(self):
        config.validate_config()

        config.PAYMENT_LINK = ""
        with self.assertRaisesRegex(RuntimeError, "PAYMENT_LINK"):
            config.validate_config()

        config.PAYMENT_LINK = "http://pay.example/subscription"
        with self.assertRaisesRegex(RuntimeError, "https://"):
            config.validate_config()

    def test_private_prompt_sends_external_payment_link_button(self):
        sent_messages = []
        bot_app.storage.record_prompt = lambda *args, **kwargs: {}

        def fake_send_message(chat_id, text, reply_markup=None):
            sent_messages.append(
                {"chat_id": chat_id, "text": text, "reply_markup": reply_markup}
            )

        bot_app.send_message = fake_send_message

        result = bot_app._send_private_payment_prompt(
            {"id": 42, "first_name": "Sam"},
            {"id": -1001234567890, "title": "AWS Jobs"},
            source="test",
            private_chat_id=4242,
        )

        self.assertTrue(result)
        self.assertEqual(len(sent_messages), 1)
        self.assertEqual(sent_messages[0]["chat_id"], 4242)
        self.assertIn(config.PAYMENT_LINK, sent_messages[0]["text"])
        self.assertIn("external payment-link", sent_messages[0]["text"])
        self.assertEqual(
            sent_messages[0]["reply_markup"]["inline_keyboard"][0][0]["url"],
            config.PAYMENT_LINK,
        )
        self.assertEqual(
            sent_messages[0]["reply_markup"]["inline_keyboard"][0][0]["text"],
            "Pay GBP 1.00",
        )


if __name__ == "__main__":
    unittest.main()