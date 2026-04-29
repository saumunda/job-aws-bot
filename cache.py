import redis
import json

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def job_seen(job_id):
    return r.sismember("seen_jobs", job_id)

def save_job(job_id):
    r.sadd("seen_jobs", job_id)

def save_heartbeat():
    r.set("bot_alive", "1", ex=60)

def is_alive():
    return r.get("bot_alive") == "1"
