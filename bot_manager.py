"""
bot_manager.py
EC2 Bot Manager Service
(Restructured — logic unchanged)
"""

import time
import datetime
import threading

from config import *
from telegram import send
import worker
from health_monitor import monitor


# =====================================================
# SERVICES
# =====================================================

def heartbeat():
    while True:
        send(
            f"✅ *BOT LIVE*\n"
            f"⏰ {datetime.datetime.now().strftime('%H:%M:%S')}"
        )
        time.sleep(HEARTBEAT_INTERVAL)


def no_job_alert():
    while True:
        idle = time.time() - worker.last_job_found

        if idle > NO_JOB_ALERT_INTERVAL:
            send("📭 No jobs available right now.")
            time.sleep(NO_JOB_ALERT_INTERVAL)
        else:
            time.sleep(60)


def watchdog():
    while True:
        idle = time.time() - worker.last_run_time

        if idle > BOT_TIMEOUT:
            send("🚨 Bot frozen → restarting workers")
            worker.start_workers()

        time.sleep(15)


# =====================================================
# BOT STARTUP
# =====================================================

def start_enterprise_bot():

    # start workers
    worker.start_workers()

    # start health monitor
    threading.Thread(
        target=monitor,
        daemon=True,
        name="HealthMonitor"
    ).start()

    # start heartbeat service
    threading.Thread(
        target=heartbeat,
        daemon=True,
        name="Heartbeat"
    ).start()

    # start no-job alert service
    threading.Thread(
        target=no_job_alert,
        daemon=True,
        name="NoJobAlert"
    ).start()

    # start watchdog
    threading.Thread(
        target=watchdog,
        daemon=True,
        name="Watchdog"
    ).start()


# =====================================================
# EC2 ENTRYPOINT
# =====================================================

def main():
    start_enterprise_bot()

    # keep service alive (systemd requirement)
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
