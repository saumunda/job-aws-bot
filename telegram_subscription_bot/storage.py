import json
import threading
from datetime import datetime, timedelta, timezone

from config import SUBSCRIPTION_DATA_FILE, SUBSCRIPTION_DURATION_DAYS


_lock = threading.Lock()


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.isoformat(timespec="seconds")


def _empty():
    return {"users": {}}


def _load():
    if not SUBSCRIPTION_DATA_FILE.exists():
        return _empty()

    with SUBSCRIPTION_DATA_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _save(data):
    SUBSCRIPTION_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = SUBSCRIPTION_DATA_FILE.with_suffix(".tmp")

    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)

    tmp_path.replace(SUBSCRIPTION_DATA_FILE)


def _user_record(data, user_id):
    return data["users"].setdefault(str(user_id), {})


def record_prompt(user, source, source_chat=None, private_chat_id=None):
    with _lock:
        data = _load()
        record = _user_record(data, user["id"])
        record.update(
            {
                "user_id": user["id"],
                "username": user.get("username"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "last_prompt_source": source,
                "last_prompted_at": _iso(_now()),
            }
        )

        if source_chat:
            record["source_chat_id"] = source_chat.get("id")
            record["source_chat_title"] = source_chat.get("title")
            record["source_chat_username"] = source_chat.get("username")

        if private_chat_id:
            record["private_chat_id"] = private_chat_id

        _save(data)
        return record


def record_delivery_failure(user_id, description):
    with _lock:
        data = _load()
        record = _user_record(data, user_id)
        record["last_delivery_failed_at"] = _iso(_now())
        record["last_delivery_error"] = description
        _save(data)


def record_join_request(user, chat, private_chat_id):
    with _lock:
        data = _load()
        record = _user_record(data, user["id"])
        record.update(
            {
                "user_id": user["id"],
                "username": user.get("username"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "pending_join_chat_id": chat.get("id"),
                "pending_join_chat_title": chat.get("title"),
                "private_chat_id": private_chat_id,
                "join_requested_at": _iso(_now()),
            }
        )
        _save(data)
        return record


def record_paid(user_id, payment):
    paid_until = _now() + timedelta(days=SUBSCRIPTION_DURATION_DAYS)

    with _lock:
        data = _load()
        record = _user_record(data, user_id)
        record.update(
            {
                "paid": True,
                "paid_at": _iso(_now()),
                "paid_until": _iso(paid_until),
                "payment_currency": payment.get("currency"),
                "payment_total_amount": payment.get("total_amount"),
                "telegram_payment_charge_id": payment.get("telegram_payment_charge_id"),
                "provider_payment_charge_id": payment.get("provider_payment_charge_id"),
            }
        )
        _save(data)
        return record