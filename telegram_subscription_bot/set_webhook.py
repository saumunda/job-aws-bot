import os

import requests

import config


ALLOWED_UPDATES = [
    "chat_join_request",
    "chat_member",
    "message",
    "pre_checkout_query",
]


def main():
    config.validate_config()
    webhook_url = os.getenv("WEBHOOK_URL", "").strip()
    if not webhook_url:
        raise RuntimeError("Missing WEBHOOK_URL")

    payload = {
        "url": webhook_url,
        "allowed_updates": ALLOWED_UPDATES,
        "drop_pending_updates": True,
    }
    if config.WEBHOOK_SECRET_TOKEN:
        payload["secret_token"] = config.WEBHOOK_SECRET_TOKEN

    response = requests.post(
        f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/setWebhook",
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    main()