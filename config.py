import os

GRAPHQL_URL = "https://qy64m4juabaffl7tjakii4gdoa.appsync-api.eu-west-1.amazonaws.com/graphql"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_IDS = [c.strip() for c in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if c.strip()]

AMAZON_ENABLED = os.getenv("AMAZON_ENABLED", "1") == "1"
TLS_ENABLED = os.getenv("TLS_ENABLED", "1") == "1"
TLS_CENTRE_NAME = os.getenv("TLS_CENTRE_NAME", "Manchester")
TLS_APPOINTMENT_URL = os.getenv(
    "TLS_APPOINTMENT_URL",
    "https://cmp.osano.com/AzqL4lT4Pea7o2XE9/c9db9abf-709d-4404-9b82-fbe51b312b5f/osano.js",
)
TLS_COOKIE = os.getenv("TLS_COOKIE", "")
TLS_AUTHORIZATION = os.getenv("TLS_AUTHORIZATION", "")
TLS_POLL_MIN = int(os.getenv("TLS_POLL_MIN", "20"))
TLS_POLL_MAX = int(os.getenv("TLS_POLL_MAX", "40"))

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

MAINTENANCE_ENABLED = os.getenv("MAINTENANCE_ENABLED", "1") == "1"
MAINTENANCE_TIME = os.getenv("MAINTENANCE_TIME", "08:00")
MAINTENANCE_MESSAGE = os.getenv(
    "MAINTENANCE_MESSAGE",
    "🚧 Bot is under maintenance and has been stopped until further notice.",
)
