import time
import os

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

_seen_jobs = set()
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
        return r.sismember("seen_jobs", job_id)
    return job_id in _seen_jobs

def save_job(job_id):
    if _redis_available():
        r.sadd("seen_jobs", job_id)
    else:
        _seen_jobs.add(job_id)

def clear_seen_jobs():
    if _redis_available():
        r.delete("seen_jobs")
    else:
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
