import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHANNEL_CHAT_ID = os.getenv("CHANNEL_CHAT_ID", "").strip()
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN", "").strip()

TELEGRAM_PROVIDER_TOKEN = os.getenv("TELEGRAM_PROVIDER_TOKEN", "").strip()
PAYMENT_LINK = os.getenv("PAYMENT_LINK", "").strip()

SUBSCRIPTION_PRICE_PENCE = int(os.getenv("SUBSCRIPTION_PRICE_PENCE", "100"))
SUBSCRIPTION_CURRENCY = os.getenv("SUBSCRIPTION_CURRENCY", "GBP").strip().upper()
SUBSCRIPTION_DURATION_DAYS = int(os.getenv("SUBSCRIPTION_DURATION_DAYS", "365"))

SUBSCRIPTION_TITLE = os.getenv(
    "SUBSCRIPTION_TITLE",
    "1 Year Channel Subscription",
).strip()
SUBSCRIPTION_DESCRIPTION = os.getenv(
    "SUBSCRIPTION_DESCRIPTION",
    "Pay GBP 1.00 for one year of channel access.",
).strip()

APPROVE_JOIN_REQUESTS_AFTER_PAYMENT = (
    os.getenv("APPROVE_JOIN_REQUESTS_AFTER_PAYMENT", "1") == "1"
)

SUBSCRIPTION_DATA_FILE = Path(
    os.getenv("SUBSCRIPTION_DATA_FILE", BASE_DIR / "data" / "subscribers.json")
)
PORT = int(os.getenv("PORT", "8010"))


def validate_config():
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not CHANNEL_CHAT_ID:
        missing.append("CHANNEL_CHAT_ID")
    if not TELEGRAM_PROVIDER_TOKEN and not PAYMENT_LINK:
        missing.append("TELEGRAM_PROVIDER_TOKEN or PAYMENT_LINK")

    if missing:
        raise RuntimeError("Missing required config: " + ", ".join(missing))