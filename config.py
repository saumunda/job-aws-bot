import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_IDS = [c.strip() for c in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if c.strip()]

AMAZON_ENABLED = os.getenv("AMAZON_ENABLED", "1") == "1"

PRIORITY_CITIES = [
    "Sheffield",
    "Rotherham",
    "Chesterfield",
    "Leeds",
    "Manchester"
]

FAST_MIN = 5
FAST_MAX = 5
BACKOFF_MIN = 8
BACKOFF_MAX = 12

BOT_TIMEOUT = 40
HEARTBEAT_INTERVAL = 3600
NO_JOB_ALERT_INTERVAL = 600   # 10 minutes

MAINTENANCE_ENABLED = os.getenv("MAINTENANCE_ENABLED", "0") == "1"
MAINTENANCE_TIME = os.getenv("MAINTENANCE_TIME", "08:00")
MAINTENANCE_MESSAGE = os.getenv(
    "MAINTENANCE_MESSAGE",
    "🚧 Bot is under maintenance and has been stopped until further notice.",
)
