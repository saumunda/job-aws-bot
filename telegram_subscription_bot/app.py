from datetime import datetime, timezone

from flask import Flask, jsonify, request

import config
import storage
from telegram_api import (
    TelegramAPIError,
    answer_chat_join_request_query,
    answer_pre_checkout_query,
    approve_chat_join_request,
    payment_link_keyboard,
    send_invoice,
    send_message,
)


app = Flask(__name__)

MEMBER_STATUSES = {"creator", "administrator", "member"}


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


def _payment_text(user, chat):
    channel_name = chat.get("title") or chat.get("username") or "the channel"
    lines = [
        f"Hi {_display_name(user)}, thanks for subscribing to {channel_name}.",
        "",
        (
            f"Your one-year subscription is {_amount_label()} "
            f"for {config.SUBSCRIPTION_DURATION_DAYS} days."
        ),
    ]

    if config.PAYMENT_LINK:
        lines.extend(["", f"Pay here: {config.PAYMENT_LINK}"])
    else:
        lines.extend(["", "Tap the invoice below to pay securely in Telegram."])

    lines.extend(["", "This payment message was sent only to you."])
    return "\n".join(lines)


def _send_private_payment_prompt(user, chat, source, private_chat_id=None):
    chat_id = private_chat_id or user["id"]
    storage.record_prompt(user, source, chat, chat_id)

    try:
        if config.TELEGRAM_PROVIDER_TOKEN:
            send_message(chat_id, _payment_text(user, chat))
            send_invoice(chat_id, user["id"])
        else:
            send_message(chat_id, _payment_text(user, chat), payment_link_keyboard())
    except TelegramAPIError as exc:
        storage.record_delivery_failure(user["id"], exc.description)
        app.logger.warning("Private payment prompt failed: %s", exc)
        return False

    return True


def _handle_join_request(join_request):
    chat = join_request.get("chat", {})
    user = join_request.get("from", {})
    private_chat_id = join_request.get("user_chat_id") or user.get("id")

    if not user.get("id") or not _target_chat_matches(chat):
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
    chat = chat_member_update.get("chat", {})
    old_member = chat_member_update.get("old_chat_member", {})
    new_member = chat_member_update.get("new_chat_member", {})
    user = new_member.get("user", {})

    if not user.get("id") or not _target_chat_matches(chat):
        return

    joined = not _is_member(old_member) and _is_member(new_member)
    if joined:
        _send_private_payment_prompt(user, chat, source="chat_member")


def _handle_pre_checkout_query(query):
    answer_pre_checkout_query(query["id"], ok=True)


def _handle_successful_payment(message):
    user = message.get("from", {})
    payment = message.get("successful_payment", {})
    if not user.get("id"):
        return

    record = storage.record_paid(user["id"], payment)
    pending_chat_id = record.get("pending_join_chat_id")
    approved = False

    if config.APPROVE_JOIN_REQUESTS_AFTER_PAYMENT and pending_chat_id:
        try:
            approve_chat_join_request(pending_chat_id, user["id"])
            approved = True
        except TelegramAPIError as exc:
            app.logger.warning("Could not approve join request: %s", exc)

    paid_until = record.get("paid_until", "")
    message_lines = [
        "Payment received. Thank you.",
        f"Your subscription is active until {paid_until}.",
    ]
    if approved:
        message_lines.append("Your join request has been approved.")

    send_message(message["chat"]["id"], "\n".join(message_lines))


def _handle_start(message):
    user = message.get("from", {})
    chat = message.get("chat", {})
    if chat.get("type") != "private" or not user.get("id"):
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    send_message(
        chat["id"],
        (
            "Private payment messages are enabled for this bot.\n"
            f"Start confirmed at {now}.\n\n"
            "When you join or request access to the channel, I will send the "
            "GBP 1.00 yearly subscription payment here."
        ),
    )


def process_update(update):
    if "chat_join_request" in update:
        _handle_join_request(update["chat_join_request"])

    if "chat_member" in update:
        _handle_chat_member(update["chat_member"])

    if "pre_checkout_query" in update:
        _handle_pre_checkout_query(update["pre_checkout_query"])

    message = update.get("message")
    if message:
        if "successful_payment" in message:
            _handle_successful_payment(message)
        elif message.get("text", "").startswith("/start"):
            _handle_start(message)


@app.route("/")
def home():
    return "Telegram subscription bot running"


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


if __name__ == "__main__":
    config.validate_config()
    app.run(host="0.0.0.0", port=config.PORT)