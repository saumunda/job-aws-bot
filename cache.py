import os
import threading
import time

import redis
from redis.exceptions import RedisError


_redis_url = os.getenv("REDIS_URL")
_redis_enabled = os.getenv("USE_REDIS") == "1" or bool(_redis_url)
r = (
    redis.Redis.from_url(
        _redis_url,
        decode_responses=True,
        socket_connect_timeout=0.2,
        socket_timeout=0.2,
    )
    if _redis_url
    else redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
        socket_connect_timeout=0.2,
        socket_timeout=0.2,
    )
)

SEEN_JOB_TTL_SECONDS = int(os.getenv("SEEN_JOB_TTL_SECONDS", "3600"))
_seen_jobs = {}
_seen_jobs_lock = threading.Lock()
_heartbeat_expires_at = 0


def _redis_available():
    if not _redis_enabled:
        return False

    try:
        return r.ping()
    except RedisError:
        return False


def job_seen(job_id):
    if _redis_available():
        return r.exists(f"seen_job:{job_id}") == 1

    with _seen_jobs_lock:
        expires_at = _seen_jobs.get(job_id)
        if expires_at is None:
            return False
        if expires_at <= time.time():
            del _seen_jobs[job_id]
            return False
        return True


def save_job(job_id):
    if _redis_available():
        r.set(f"seen_job:{job_id}", "1", ex=SEEN_JOB_TTL_SECONDS)
        return

    with _seen_jobs_lock:
        _seen_jobs[job_id] = time.time() + SEEN_JOB_TTL_SECONDS


def reserve_job(job_id):
    """Reserve a job for one hour and return whether it has not been alerted yet."""
    if _redis_available():
        return bool(
            r.set(
                f"seen_job:{job_id}",
                "1",
                ex=SEEN_JOB_TTL_SECONDS,
                nx=True,
            )
        )

    with _seen_jobs_lock:
        expires_at = _seen_jobs.get(job_id)
        if expires_at is not None and expires_at > time.time():
            return False

        _seen_jobs[job_id] = time.time() + SEEN_JOB_TTL_SECONDS
        return True


def clear_seen_jobs():
    if _redis_available():
        for key in r.scan_iter("seen_job:*"):
            r.delete(key)
    else:
        with _seen_jobs_lock:
            _seen_jobs.clear()


def save_heartbeat():
    global _heartbeat_expires_at
    if _redis_available():
        r.set("bot_alive", "1", ex=60)
    else:
        _heartbeat_expires_at = time.time() + 60


def is_alive():
    if _redis_available():
        return r.get("bot_alive") == "1"
    return time.time() < _heartbeat_expires_at