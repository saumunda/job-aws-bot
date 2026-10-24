import os

from dotenv import load_dotenv


load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_IDS = [c.strip() for c in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if c.strip()]

AMAZON_ENABLED = os.getenv("AMAZON_ENABLED", "1") == "1"
JOB_SEARCH_INTERVAL_SECONDS = int(os.getenv("JOB_SEARCH_INTERVAL_SECONDS", "5"))
if JOB_SEARCH_INTERVAL_SECONDS < 1:
    raise RuntimeError("JOB_SEARCH_INTERVAL_SECONDS must be at least 1")

PRIORITY_CITIES = [
    "Sheffield",
    "Rotherham",
    "Chesterfield",
    "Leeds",
    "Manchester"
]

BOT_TIMEOUT = 40
HEARTBEAT_INTERVAL = 3600

MAINTENANCE_ENABLED = os.getenv("MAINTENANCE_ENABLED", "0") == "1"
MAINTENANCE_TIME = os.getenv("MAINTENANCE_TIME", "00:00")
MAINTENANCE_MESSAGE = os.getenv(
    "MAINTENANCE_MESSAGE",
    "🚧 Bot is under maintenance and has been stopped until further notice.",
)
