import datetime
import random
import threading
import time

import requests

from cache import job_seen, save_heartbeat, save_job
from config import (
    BACKOFF_MAX,
    BACKOFF_MIN,
    FAST_MAX,
    FAST_MIN,
    PRIORITY_CITIES,
)
from data import GRAPHQL_URL, HEADERS, JOB_PAGE_URL, SEARCH_PAYLOAD
from telegram import send


WORKER_COUNT = 1

last_run_time = time.time()
last_job_found = time.time()
_workers_started = False
_workers_lock = threading.Lock()


def fetch_jobs():
    response = requests.post(
        GRAPHQL_URL,
        headers=HEADERS,
        json=SEARCH_PAYLOAD,
        timeout=20,
    )

    if response.status_code != 200:
        print("GraphQL error:", response.status_code, response.text[:300])
        return []

    data = response.json()
    return (
        data.get("data", {})
        .get("searchJobCardsByLocation", {})
        .get("jobCards", [])
    )


def format_job(job):
    job_id = job.get("jobId")
    city = job.get("city", "")
    state = job.get("state", "")
    postal_code = job.get("postalCode", "")
    pay_rate = job.get("totalPayRateMax", "N/A")

    return (
        f"*{job.get('jobTitle', 'Unknown')}*\n"
        f"Location: {city}, {state}, {postal_code}\n"
        f"Pay: GBP {pay_rate}/hr\n"
        f"Job type: {job.get('jobType', '')}\n"
        f"Employment: {job.get('employmentType', '')}\n"
        "Apply: "
        f"https://www.jobsatamazon.co.uk/app#/jobDetail?jobId={job_id}&locale=en-GB"
    )


def priority_score(job):
    city = (job.get("city") or "").lower()
    for index, priority_city in enumerate(PRIORITY_CITIES):
        if priority_city.lower() in city:
            return index
    return len(PRIORITY_CITIES)


def run_once():
    global last_job_found, last_run_time

    last_run_time = time.time()
    save_heartbeat()
    print("Running job check:", datetime.datetime.now().isoformat(timespec="seconds"))

    jobs = sorted(fetch_jobs(), key=priority_score)
    if jobs:
        last_job_found = time.time()

    for job in jobs:
        job_id = job.get("jobId")
        if not job_id or job_seen(job_id):
            continue

        save_job(job_id)
        send(format_job(job))


def worker_loop():
    while True:
        try:
            run_once()
            sleep_for = random.randint(FAST_MIN, FAST_MAX)
        except Exception as exc:
            print("Worker error:", exc)
            sleep_for = random.randint(BACKOFF_MIN, BACKOFF_MAX)

        time.sleep(sleep_for)


def start_workers():
    global _workers_started

    with _workers_lock:
        if _workers_started:
            return

        for index in range(WORKER_COUNT):
            threading.Thread(
                target=worker_loop,
                daemon=True,
                name=f"AmazonWorker-{index + 1}",
            ).start()

        _workers_started = True
if __name__ == "__main__":
    start_workers()
    while True:
        time.sleep(60)