import os

GRAPHQL_URL = "https://qy64m4juabaffl7tjakii4gdoa.appsync-api.eu-west-1.amazonaws.com/graphql"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_IDS = [c.strip() for c in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if c.strip()]

PRIORITY_CITIES = [
    "Sheffield",
    "Rotherham",
    "Chesterfield",
    "Leeds",
    "Manchester"
]

FAST_MIN = 3
FAST_MAX = 5
BACKOFF_MIN = 8
BACKOFF_MAX = 12

BOT_TIMEOUT = 40
HEARTBEAT_INTERVAL = 3600
NO_JOB_ALERT_INTERVAL = 600   # 10 minutes
