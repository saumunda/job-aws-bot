"""
bot_manager.py
EC2 Bot Manager Service
(Restructured — logic unchanged)
"""

import time
import datetime
import threading
import os
import tempfile

if os.name == "nt":
    import msvcrt
else:
    import fcntl

from config import *
from cache import clear_seen_jobs
from telegram import send
import worker2 as worker
from health_monitor import monitor


_startup_lock = threading.Lock()
_started = False
_process_lock_file = None
_stop_event = threading.Event()

_FUEL_BOT_LINES = (
    "Every alert has a little engine behind it. Help keep it scanning for the next opportunity.",
    "Jobs move fast. A small contribution helps keep the bot awake and watching.",
    "The next alert could change someone's week. Fuel the bot and keep the search running.",
)


def _acquire_process_lock():
    """
    Gunicorn starts one copy of this module per worker process. Keep exactly one
    process responsible for the background bot so Telegram posts are not doubled.
    """
    global _process_lock_file

    lock_path = os.path.join(tempfile.gettempdir(), "job-bot-amazon.lock")
    lock_file = open(lock_path, "w")

    try:
        if os.name == "nt":
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock_file.close()
        return False

    _process_lock_file = lock_file
    return True


# =====================================================
# SERVICES
# =====================================================

def _fuel_bot_message(index):
    line = _FUEL_BOT_LINES[index % len(_FUEL_BOT_LINES)]
    return (
        "*Fuel the Bot*\n\n"
        f"{line}\n\n"
        f"[Support the bot with Stripe]({STRIPE_PAYMENT_LINK})"
    )


def heartbeat():
    while not _stop_event.is_set():
        clear_seen_jobs()
        send(
            f"✅ *BOT LIVE*\n"
            f"⏰ {datetime.datetime.now().strftime('%H:%M:%S')}"
        )

        if _stop_event.wait(HEARTBEAT_INTERVAL):
            break


def fuel_bot_reminder():
    """Send the first Stripe reminder after one hour, then once per interval."""
    reminder_index = 0

    while not _stop_event.wait(FUEL_BOT_REMINDER_INTERVAL_SECONDS):
        if _stop_event.is_set():
            break
        send(_fuel_bot_message(reminder_index))
        reminder_index += 1


def no_job_alert():
    while not _stop_event.is_set():
        idle = time.time() - worker.last_job_found

        if idle > NO_JOB_ALERT_INTERVAL:
            send("📭 No jobs available right now.")
            if _stop_event.wait(NO_JOB_ALERT_INTERVAL):
                break
        else:
            if _stop_event.wait(60):
                break


def watchdog():
    while not _stop_event.is_set():
        idle = time.time() - worker.last_run_time

        if idle > BOT_TIMEOUT:
            send("🚨 Bot frozen → restarting workers")
            worker.start_workers()

        if _stop_event.wait(15):
            break


def _seconds_until_target(time_str):
    now = datetime.datetime.now()
    target_time = datetime.datetime.strptime(time_str, "%H:%M").time()
    target = datetime.datetime.combine(now.date(), target_time)
    if target <= now:
        target += datetime.timedelta(days=1)
    return (target - now).total_seconds()


def stop_bot():
    send(MAINTENANCE_MESSAGE)
    worker.stop_workers()
    _stop_event.set()


def maintenance_scheduler():
    if not MAINTENANCE_ENABLED:
        return

    delay = _seconds_until_target(MAINTENANCE_TIME)
    time.sleep(delay)
    if _stop_event.is_set():
        return

    stop_bot()


# =====================================================
# BOT STARTUP
# =====================================================

def start_enterprise_bot():
    global _started

    with _startup_lock:
        if _started:
            return

        if not _acquire_process_lock():
            print("Bot already running in another process")
            return

        _started = True

    # start workers
    if AMAZON_ENABLED:
        worker.start_workers()

    # start health monitor
    threading.Thread(
        target=monitor,
        args=(_stop_event,),
        daemon=True,
        name="HealthMonitor"
    ).start()

    # start heartbeat service
    threading.Thread(
        target=heartbeat,
        daemon=True,
        name="Heartbeat"
    ).start()

    # Delay the first Stripe message for one full interval after startup.
    if FUEL_BOT_REMINDER_ENABLED and STRIPE_PAYMENT_LINK:
        threading.Thread(
            target=fuel_bot_reminder,
            daemon=True,
            name="FuelBotReminder"
        ).start()

    # start watchdog
    threading.Thread(
        target=watchdog,
        daemon=True,
        name="Watchdog"
    ).start()

    # schedule maintenance stop at configured time
    threading.Thread(
        target=maintenance_scheduler,
        daemon=True,
        name="MaintenanceScheduler"
    ).start()


# =====================================================
# EC2 ENTRYPOINT
# =====================================================

def main():
    start_enterprise_bot()

    # keep service alive until maintenance stop triggers
    while not _stop_event.wait(3600):
        pass


if __name__ == "__main__":
    main()
