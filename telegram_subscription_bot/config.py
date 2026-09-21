import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHANNEL_CHAT_ID = os.getenv("CHANNEL_CHAT_ID", "").strip()
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN", "").strip()

PAYMENT_LINK = os.getenv("PAYMENT_LINK", "").strip()
PAYMENT_REMINDER_ENABLED = os.getenv("PAYMENT_REMINDER_ENABLED", "1") == "1"
PAYMENT_REMINDER_INTERVAL_SECONDS = int(
    os.getenv("PAYMENT_REMINDER_INTERVAL_SECONDS", "3600")
)
PAYMENT_REMINDER_CHAT_ID = (
    os.getenv("PAYMENT_REMINDER_CHAT_ID", "").strip() or CHANNEL_CHAT_ID
)

SUBSCRIPTION_PRICE_PENCE = int(os.getenv("SUBSCRIPTION_PRICE_PENCE", "100"))
SUBSCRIPTION_CURRENCY = os.getenv("SUBSCRIPTION_CURRENCY", "GBP").strip().upper()
SUBSCRIPTION_DURATION_DAYS = int(os.getenv("SUBSCRIPTION_DURATION_DAYS", "365"))

SUBSCRIPTION_DATA_FILE = Path(
    os.getenv("SUBSCRIPTION_DATA_FILE", BASE_DIR / "data" / "subscribers.json")
)
PORT = int(os.getenv("PORT", "8010"))


STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
PAYMENTS_DB = Path(os.getenv("PAYMENTS_DB", BASE_DIR / "data" / "payments.sqlite3"))


def validate_config():
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not CHANNEL_CHAT_ID:
        missing.append("CHANNEL_CHAT_ID")
    if STRIPE_SECRET_KEY:
        for name in ("STRIPE_WEBHOOK_SECRET", "PUBLIC_BASE_URL", "WEBHOOK_SECRET_TOKEN"):
            if not globals()[name]:
                missing.append(name)
    elif not PAYMENT_LINK:
        missing.append("PAYMENT_LINK")

    if missing:
        raise RuntimeError("Missing required config: " + ", ".join(missing))

    if PAYMENT_REMINDER_INTERVAL_SECONDS < 60:
        raise RuntimeError("PAYMENT_REMINDER_INTERVAL_SECONDS must be at least 60")

    if STRIPE_SECRET_KEY:
        if not PUBLIC_BASE_URL.startswith("https://"):
            raise RuntimeError("PUBLIC_BASE_URL must start with https://")
        if SUBSCRIPTION_PRICE_PENCE <= 0 or SUBSCRIPTION_DURATION_DAYS <= 0:
            raise RuntimeError("Payment amount and duration must be positive")
    elif not PAYMENT_LINK.startswith("https://"):
        raise RuntimeError("PAYMENT_LINK must start with https://")