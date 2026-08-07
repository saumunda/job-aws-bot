import requests
from config import TELEGRAM_BOT_TOKEN, CHAT_IDS

def send(msg):
    for chat_id in CHAT_IDS:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
                timeout=30
            )
        except Exception as e:
            print("Telegram error:", e)
            return "Telegram error:", e"
