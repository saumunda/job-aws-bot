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


def answer_chat_join_request_query(query_id, result="queue"):
    return _post(
        "answerChatJoinRequestQuery",
        {"chat_join_request_query_id": query_id, "result": result},
    )


def approve_chat_join_request(chat_id, user_id):
    return _post("approveChatJoinRequest", {"chat_id": chat_id, "user_id": user_id})


def get_chat_member(chat_id, user_id):
    return _post("getChatMember", {"chat_id": chat_id, "user_id": user_id})


def payment_link_keyboard(url=None):
    url = url or config.PAYMENT_LINK
    if not url:
        return None

    amount = config.SUBSCRIPTION_PRICE_PENCE / 100
    return {
        "inline_keyboard": [
            [
                {
                    "text": f"Pay {config.SUBSCRIPTION_CURRENCY} {amount:.2f}",
                    "url": url,
                }
            ]
        ]
    }


def dumps_for_log(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))