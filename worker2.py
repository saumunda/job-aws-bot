import datetime
import random
import threading
import time

import requests

from cache import job_seen, save_heartbeat, save_job
from config import BACKOFF_MAX, BACKOFF_MIN, FAST_MAX, FAST_MIN, GRAPHQL_URL
from telegram import send


JOB_PAGE_URL = (
    "https://www.jobsatamazon.co.uk/app#/jobSearch"
    "?query=Warehouse%20Operative&locale=en-GB"
)

WORKER_COUNT = 1

last_run_time = time.time()
last_job_found = time.time()
_workers_started = False
_workers_lock = threading.Lock()


def get_auth_token():
    try:
        session = requests.Session()
        response = session.get(
            JOB_PAGE_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "text/html",
                "Referer": "https://www.jobsatamazon.co.uk/",
            },
            timeout=20,
        )
        response.raise_for_status()

        for cookie in session.cookies:
            if "session" in cookie.name.lower():
                return "Bearer " + cookie.value
    except Exception as exc:
        print("Token error:", exc)

    return None


def fetch_jobs(auth_token):
    payload = {
        "operationName": "searchJobCardsByLocation",
        "variables": {
            "searchJobRequest": {
                "locale": "en-GB",
                "country": "United Kingdom",
                "keyWords": "Warehouse Operative",
                "equalFilters": [],
                "containFilters": [
                    {"key": "isPrivateSchedule", "val": ["true", "false"]}
                ],
                "rangeFilters": [],
                "orFilters": [],
                "dateFilters": [],
                "sorters": [{"fieldName": "totalPayRateMax", "ascending": "false"}],
                "pageSize": 20,
                "consolidateSchedule": True,
            }
        },
        "query": """
        query searchJobCardsByLocation($searchJobRequest: SearchJobRequest!) {
          searchJobCardsByLocation(searchJobRequest: $searchJobRequest) {
            jobCards {
              jobId
              jobTitle
              city
              state
              postalCode
              jobType
              employmentType
              totalPayRateMax
            }
          }
        }
        """,
    }

    headers = {
        "Authorization": auth_token,
        "Content-Type": "application/json",
        "Origin": "https://www.jobsatamazon.co.uk",
        "Referer": "https://www.jobsatamazon.co.uk/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }

    response = requests.post(
        GRAPHQL_URL,
        headers=headers,
        json=payload,
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
    location = ", ".join(part for part in [city, state, postal_code] if part)

    return (
        f"🚨 *NEW AMAZON JOB ALERT*\n\n"
        f"💼 *{job.get('jobTitle', 'Unknown')}*\n"
        f"📍 `Location:` {location or 'N/A'}\n"
        f"💷 `Pay:` GBP {pay_rate}/hr\n"
        f"🕒 `Job type:` {job.get('jobType', 'N/A')}\n"
        f"📄 `Employment:` {job.get('employmentType', 'N/A')}\n"
        "🔗 `Apply:` "
        f"[Click here](https://www.jobsatamazon.co.uk/app#/jobDetail?jobId={job_id}&locale=en-GB)"
    )


def run_once():
    global last_job_found, last_run_time

    last_run_time = time.time()
    save_heartbeat()
    print("Running job check:", datetime.datetime.now().isoformat(timespec="seconds"))

    token = get_auth_token()
    if not token:
        print("Token error")
        return

    jobs = fetch_jobs(token)
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
                name=f"AmazonWorker2-{index + 1}",
            ).start()

        _workers_started = True
