import json

import requests

import config


class TelegramAPIError(RuntimeError):
    def __init__(self, method, description, status_code=None):
        self.method = method
        self.description = description
        self.status_code = status_code
        super().__init__(f"{method} failed: {description}")


def _url(method):
    return f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/{method}"


def _post(method, payload):
    response = requests.post(_url(method), json=payload, timeout=15)

    try:
        data = response.json()
    except ValueError as exc:
        raise TelegramAPIError(method, response.text[:300], response.status_code) from exc

    if not data.get("ok"):
        raise TelegramAPIError(
            method,
            data.get("description", "unknown Telegram API error"),
            response.status_code,
        )

    return data["result"]


def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    return _post("sendMessage", payload)


def send_invoice(chat_id, user_id):
    return _post(
        "sendInvoice",
        {
            "chat_id": chat_id,
            "title": config.SUBSCRIPTION_TITLE[:32],
            "description": config.SUBSCRIPTION_DESCRIPTION[:255],
            "payload": f"year_subscription:{user_id}",
            "provider_token": config.TELEGRAM_PROVIDER_TOKEN,
            "currency": config.SUBSCRIPTION_CURRENCY,
            "prices": [
                {
                    "label": config.SUBSCRIPTION_TITLE[:32],
                    "amount": config.SUBSCRIPTION_PRICE_PENCE,
                }
            ],
            "start_parameter": "year-subscription",
        },
    )


def answer_pre_checkout_query(query_id, ok=True, error_message=None):
    payload = {"pre_checkout_query_id": query_id, "ok": ok}
    if error_message:
        payload["error_message"] = error_message

    return _post("answerPreCheckoutQuery", payload)


def approve_chat_join_request(chat_id, user_id):
    return _post("approveChatJoinRequest", {"chat_id": chat_id, "user_id": user_id})


def answer_chat_join_request_query(query_id, result="queue"):
    return _post(
        "answerChatJoinRequestQuery",
        {"chat_join_request_query_id": query_id, "result": result},
    )


def payment_link_keyboard():
    if not config.PAYMENT_LINK:
        return None

    return {
        "inline_keyboard": [
            [
                {
                    "text": f"Pay {config.SUBSCRIPTION_CURRENCY} {config.SUBSCRIPTION_PRICE_PENCE / 100:.2f}",
                    "url": config.PAYMENT_LINK,
                }
            ]
        ]
    }


def dumps_for_log(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))