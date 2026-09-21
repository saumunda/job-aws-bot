from datetime import datetime, timezone
import os
import tempfile
import threading

from flask import Flask, jsonify, request

import config
import storage
import payments
import stripe
from telegram_api import (
    TelegramAPIError,
    answer_chat_join_request_query,
    payment_link_keyboard,
    send_message,
)


app = Flask(__name__)

MEMBER_STATUSES = {"creator", "administrator", "member"}

_PAYMENT_REMINDER_MESSAGES = (
    "Keep the job alerts running while you focus on the next opportunity.",
    "A small top-up keeps this job-hunting engine scanning for your next role.",
    "Help keep the alerts awake, quick, and ready for the next opening.",
)
_reminder_lock = threading.Lock()
_reminder_started = False
_reminder_lock_file = None


def _acquire_reminder_process_lock():
    """Ensure only one web worker posts the recurring reminder."""
    global _reminder_lock_file

    lock_path = os.path.join(tempfile.gettempdir(), "telegram-payment-reminder.lock")
    lock_file = open(lock_path, "w")
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock_file.close()
        return False

    _reminder_lock_file = lock_file
    return True


def _target_chat_matches(chat):
    configured = config.CHANNEL_CHAT_ID
    if not configured:
        return False

    chat_id = chat.get("id")
    username = chat.get("username")

    return configured == str(chat_id) or configured == f"@{username}"


def _is_member(chat_member):
    status = chat_member.get("status")
    if status in MEMBER_STATUSES:
        return True

    return status == "restricted" and chat_member.get("is_member") is True


def _display_name(user):
    return user.get("first_name") or user.get("username") or "there"


def _amount_label():
    return f"{config.SUBSCRIPTION_CURRENCY} {config.SUBSCRIPTION_PRICE_PENCE / 100:.2f}"


def _payment_reminder_text(index):
    message = _PAYMENT_REMINDER_MESSAGES[index % len(_PAYMENT_REMINDER_MESSAGES)]
    return "\n".join(
        [
            "Fuel the bot and keep the job alerts coming.",
            "",
            message,
            f"Support access for {_amount_label()}.",
        ]
    )


def _send_payment_reminder(index=0):
    if config.STRIPE_SECRET_KEY or not config.PAYMENT_REMINDER_ENABLED or not config.PAYMENT_REMINDER_CHAT_ID:
        return False

    try:
        send_message(
            config.PAYMENT_REMINDER_CHAT_ID,
            _payment_reminder_text(index),
            payment_link_keyboard(),
        )
    except TelegramAPIError as exc:
        app.logger.warning("Hourly payment reminder failed: %s", exc)
        return False

    return True


def _payment_reminder_loop():
    index = 0
    while True:
        _send_payment_reminder(index)
        index += 1
        threading.Event().wait(config.PAYMENT_REMINDER_INTERVAL_SECONDS)


def start_payment_reminders():
    global _reminder_started

    if not config.PAYMENT_REMINDER_ENABLED:
        return

    with _reminder_lock:
        if _reminder_started or not _acquire_reminder_process_lock():
            return

        threading.Thread(
            target=_payment_reminder_loop,
            daemon=True,
            name="PaymentReminder",
        ).start()
        _reminder_started = True


def _payment_text(user, chat, payment_url=None):
    channel_name = chat.get("title") or chat.get("username") or "the channel"
    lines = [
        f"Hi {_display_name(user)}, thanks for subscribing to {channel_name}.",
        "",
        (
            f"Your one-year subscription is {_amount_label()} "
            f"for {config.SUBSCRIPTION_DURATION_DAYS} days."
        ),
        "",
        f"Pay here: {payment_url or config.PAYMENT_LINK}",
        "",
        "This external payment-link message was sent only to you.",
    ]
    return "\n".join(lines)


def _send_private_payment_prompt(user, chat, source, private_chat_id=None):
    chat_id = private_chat_id or user["id"]
    if not config.STRIPE_SECRET_KEY:
        storage.record_prompt(user, source, chat, chat_id)

    try:
        url = config.PAYMENT_LINK
        if config.STRIPE_SECRET_KEY:
            url = payments.checkout_url(user["id"], chat["id"])
        send_message(chat_id, _payment_text(user, chat, url), payment_link_keyboard(url))
    except TelegramAPIError as exc:
        if not config.STRIPE_SECRET_KEY:
            storage.record_delivery_failure(user["id"], exc.description)
        app.logger.warning("Private payment prompt failed: %s", exc)
        if config.STRIPE_SECRET_KEY:
            raise  # Telegram retries the update after a transient DM failure.
        return False

    return True


def _handle_join_request(join_request):
    chat = join_request.get("chat", {})
    user = join_request.get("from", {})
    private_chat_id = join_request.get("user_chat_id") or user.get("id")

    if not user.get("id") or not _target_chat_matches(chat):
        return

    if config.STRIPE_SECRET_KEY:
        if payments.approve_if_paid(user["id"], chat["id"]):
            return
        _send_private_payment_prompt(user, chat, "chat_join_request", private_chat_id)
        return

    storage.record_join_request(user, chat, private_chat_id)

    query_id = join_request.get("query_id")
    if query_id:
        try:
            answer_chat_join_request_query(query_id, "queue")
        except TelegramAPIError as exc:
            app.logger.warning("Could not queue join request query: %s", exc)

    _send_private_payment_prompt(
        user,
        chat,
        source="chat_join_request",
        private_chat_id=private_chat_id,
    )


def _handle_chat_member(chat_member_update):
    if config.STRIPE_SECRET_KEY:
        return  # Approval generates this event too; never charge twice.
    chat = chat_member_update.get("chat", {})
    old_member = chat_member_update.get("old_chat_member", {})
    new_member = chat_member_update.get("new_chat_member", {})
    user = new_member.get("user", {})

    if not user.get("id") or not _target_chat_matches(chat):
        return

    joined = not _is_member(old_member) and _is_member(new_member)
    if joined:
        _send_private_payment_prompt(user, chat, source="chat_member")


def _handle_start(message):
    user = message.get("from", {})
    chat = message.get("chat", {})
    if chat.get("type") != "private" or not user.get("id"):
        return

    if config.STRIPE_SECRET_KEY:
        send_message(chat["id"], "Request to join the group using its approval-required invite link. "
                     "I will send a private Stripe Checkout link, then approve access after payment.")
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    send_message(
        chat["id"],
        (
            "Private payment messages are enabled for this bot.\n"
            f"Start confirmed at {now}.\n\n"
            "When you join or request access to the channel, I will send the "
            "GBP 1.00 yearly subscription payment link here."
        ),
    )


def process_update(update):
    if "chat_join_request" in update:
        _handle_join_request(update["chat_join_request"])

    if "chat_member" in update:
        _handle_chat_member(update["chat_member"])

    message = update.get("message")
    if message and message.get("text", "").startswith("/start"):
        _handle_start(message)


@app.route("/")
def home():
    return "Telegram subscription payment-link bot running"


@app.route("/health")
def health():
    return jsonify({"status": "OK"})


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    if config.WEBHOOK_SECRET_TOKEN:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if token != config.WEBHOOK_SECRET_TOKEN:
            return jsonify({"ok": False, "error": "bad secret token"}), 403

    process_update(request.get_json(force=True, silent=False))
    return jsonify({"ok": True})


@app.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    if not config.STRIPE_SECRET_KEY or not config.STRIPE_WEBHOOK_SECRET:
        return jsonify({"error": "Stripe is not configured"}), 503
    try:
        event = stripe.Webhook.construct_event(
            request.get_data(), request.headers.get("Stripe-Signature", ""),
            config.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError):
        return jsonify({"error": "Invalid Stripe signature or payload"}), 400
    if event["type"] in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
        try:
            payments.fulfill(event["data"]["object"].to_dict())
        except Exception:
            app.logger.exception("Payment fulfillment failed; webhook should retry")
            return jsonify({"error": "Fulfillment failed"}), 500
    return jsonify({"ok": True})


@app.route("/payment/success")
def payment_success():
    return "Thank you. Access is approved after Stripe confirms payment. Return to Telegram. If access is still pending, request to join again."


@app.route("/payment/cancel")
def payment_cancel():
    return "Payment cancelled. Access has not been granted. Return to Telegram to retry your payment link."


if __name__ == "__main__":
    config.validate_config()
    start_payment_reminders()
    app.run(host="0.0.0.0", port=config.PORT)