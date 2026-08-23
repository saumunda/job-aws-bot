import datetime
import hashlib
import json
import random
import re
import threading
import time

import requests

from config import (
    TLS_APPOINTMENT_URL,
    TLS_AUTHORIZATION,
    TLS_CENTRE_NAME,
    TLS_COOKIE,
    TLS_ENABLED,
    TLS_POLL_MAX,
    TLS_POLL_MIN,
)
from telegram import send


WORKER_COUNT = 1

last_run_time = time.time()
last_appointment_found = 0
_last_available_fingerprint = None
_workers_started = False
_workers_lock = threading.Lock()
_stop_event = threading.Event()


NEGATIVE_TEXT = (
    "no appointment",
    "no appointments",
    "no slot",
    "no slots",
    "not available",
    "fully booked",
    "unavailable",
)

POSITIVE_TEXT = (
    "appointment available",
    "appointments available",
    "slot available",
    "slots available",
    "available appointment",
    "available appointments",
)

APPOINTMENT_KEYS = {
    "appointment",
    "appointments",
    "available",
    "availability",
    "bookable",
    "date",
    "dates",
    "slot",
    "slots",
    "time",
    "times",
    "timeslot",
    "timeslots",
}


def _headers():
    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://fr.tlscontact.com/",
    }

    if TLS_COOKIE:
        headers["Cookie"] = TLS_COOKIE
    if TLS_AUTHORIZATION:
        headers["Authorization"] = TLS_AUTHORIZATION

    return headers


def fetch_appointment_response():
    response = requests.get(
        TLS_APPOINTMENT_URL,
        headers=_headers(),
        timeout=20,
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if "json" in content_type:
        return response.json()

    text = response.text.strip()
    try:
        return json.loads(text)
    except ValueError:
        return text


def _looks_like_date_or_time(value):
    if not isinstance(value, str):
        return False

    return bool(
        re.search(r"\b20\d{2}-\d{2}-\d{2}\b", value)
        or re.search(r"\b\d{1,2}:\d{2}\b", value)
        or re.search(
            r"\b(mon|tue|wed|thu|fri|sat|sun|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",
            value.lower(),
        )
    )


def _contains_appointment_data(value, parent_key=""):
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower()
            child_key = key_text if key_text in APPOINTMENT_KEYS else parent_key

            if key_text in {"available", "bookable"} and child is True:
                return True
            if _contains_appointment_data(child, child_key):
                return True
        return False

    if isinstance(value, list):
        if not value:
            return False

        if parent_key in APPOINTMENT_KEYS:
            return True

        return any(_contains_appointment_data(item, parent_key) for item in value)

    if parent_key in APPOINTMENT_KEYS and _looks_like_date_or_time(value):
        return True

    return False


def appointment_available(payload):
    if isinstance(payload, (dict, list)):
        return _contains_appointment_data(payload)

    text = str(payload).lower()

    if any(phrase in text for phrase in NEGATIVE_TEXT):
        return False

    return any(phrase in text for phrase in POSITIVE_TEXT)


def fingerprint(payload):
    if isinstance(payload, str):
        raw = payload
    else:
        raw = json.dumps(payload, sort_keys=True, default=str)

    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()


def format_appointment_alert(payload):
    checked_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(payload, (dict, list)):
        details = json.dumps(payload, indent=2, sort_keys=True, default=str)
    else:
        details = str(payload)
    details = details.replace("```", "'''")

    return (
        f"*TLS {TLS_CENTRE_NAME} appointment available*\n"
        f"Checked: {checked_at}\n"
        f"URL: {TLS_APPOINTMENT_URL}\n\n"
        f"```{details[:1500]}```"
    )


def run_once():
    global _last_available_fingerprint, last_appointment_found, last_run_time

    if not TLS_ENABLED:
        return

    last_run_time = time.time()
    print(
        "Running TLS appointment check:",
        datetime.datetime.now().isoformat(timespec="seconds"),
    )

    payload = fetch_appointment_response()

    if not appointment_available(payload):
        return

    last_appointment_found = time.time()
    current_fingerprint = fingerprint(payload)

    if current_fingerprint == _last_available_fingerprint:
        return

    _last_available_fingerprint = current_fingerprint
    send(format_appointment_alert(payload))


def worker_loop():
    while not _stop_event.is_set():
        try:
            run_once()
        except Exception as exc:
            print("TLS worker error:", exc)

        sleep_min = min(TLS_POLL_MIN, TLS_POLL_MAX)
        sleep_max = max(TLS_POLL_MIN, TLS_POLL_MAX)
        if _stop_event.wait(random.randint(sleep_min, sleep_max)):
            break


def stop_workers():
    _stop_event.set()


def start_workers():
    global _workers_started

    if not TLS_ENABLED:
        print("TLS worker disabled")
        return

    with _workers_lock:
        if _workers_started:
            return

        for index in range(WORKER_COUNT):
            threading.Thread(
                target=worker_loop,
                daemon=True,
                name=f"TLSWorker-{index + 1}",
            ).start()

        _workers_started = True
