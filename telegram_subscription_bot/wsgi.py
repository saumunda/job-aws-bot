import config
from app import app, start_payment_reminders


config.validate_config()
start_payment_reminders()