import time
from telegram import send
from cache import is_alive

def monitor():
    while True:
        if not is_alive():
            send("🚨 BOT OFFLINE DETECTED")
        time.sleep(30)
