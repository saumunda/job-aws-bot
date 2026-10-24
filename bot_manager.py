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
import worker2 as worker
from health_monitor import monitor


_startup_lock = threading.Lock()
_started = False
_process_lock_file = None
_stop_event = threading.Event()

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
def heartbeat():
    while not _stop_event.wait(HEARTBEAT_INTERVAL):
        clear_seen_jobs()


def watchdog():
    while not _stop_event.is_set():
        idle = time.time() - worker.last_run_time

        if idle > BOT_TIMEOUT:
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

    # Monitor health locally without sending non-job Telegram messages.
    threading.Thread(
        target=monitor,
        args=(_stop_event,),
        daemon=True,
        name="HealthMonitor"
    ).start()

    # Clear all seen jobs together once per hour without posting a status message.
    threading.Thread(
        target=heartbeat,
        daemon=True,
        name="Heartbeat"
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
