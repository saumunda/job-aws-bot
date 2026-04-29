import time
import datetime
import threading

from config import *
from telegram import send
from worker import start_workers, last_run_time, last_job_found
from health_monitor import monitor
threading.Thread(target=monitor, daemon=True).start()

def heartbeat():
    while True:
        send(
            f"✅ *BOT LIVE*\n"
            f"⏰ {datetime.datetime.now().strftime('%H:%M:%S')}"
        )
        time.sleep(HEARTBEAT_INTERVAL)


def no_job_alert():
    while True:
        idle = time.time() - last_job_found

        if idle > NO_JOB_ALERT_INTERVAL:
            send("📭 No jobs available right now.")
            time.sleep(NO_JOB_ALERT_INTERVAL)
        else:
            time.sleep(60)


def watchdog():
    while True:
        idle = time.time() - last_run_time

        if idle > BOT_TIMEOUT:
            send("🚨 Bot frozen → restarting workers")
            start_workers()

        time.sleep(15)


def start_enterprise_bot():
    start_workers()

    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=no_job_alert, daemon=True).start()
    threading.Thread(target=watchdog, daemon=True).start()
