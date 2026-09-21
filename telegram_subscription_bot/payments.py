"""Durable Checkout identity binding and retryable Telegram approval."""
from contextlib import contextmanager
import sqlite3
import time
import stripe
import config
from telegram_api import approve_chat_join_request, get_chat_member


@contextmanager
def database():
    config.PAYMENTS_DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(config.PAYMENTS_DB, timeout=30)
    db.row_factory = sqlite3.Row
    try:
        db.execute("""CREATE TABLE IF NOT EXISTS checkouts (
            session_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL, amount INTEGER NOT NULL,
            currency TEXT NOT NULL, duration INTEGER NOT NULL,
            url TEXT NOT NULL, expires_at INTEGER NOT NULL,
            paid_until INTEGER, fulfilled INTEGER NOT NULL DEFAULT 0)""")
        db.commit()
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def checkout_url(user_id, chat_id):
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute(
            "SELECT url FROM checkouts WHERE user_id=? AND chat_id=? "
            "AND paid_until IS NULL AND expires_at>? ORDER BY expires_at DESC LIMIT 1",
            (user_id, chat_id, int(time.time()) + 60),
        ).fetchone()
        if existing:
            return existing["url"]
        session = stripe.checkout.Session.create(
            api_key=config.STRIPE_SECRET_KEY,
            mode="payment",
            client_reference_id=str(user_id),
            metadata={"telegram_user_id": str(user_id), "telegram_chat_id": str(chat_id)},
            line_items=[{"price_data": {
                "currency": config.SUBSCRIPTION_CURRENCY.lower(),
                "unit_amount": config.SUBSCRIPTION_PRICE_PENCE,
                "product_data": {"name": "Telegram group access"},
            }, "quantity": 1}],
            success_url=config.PUBLIC_BASE_URL + "/payment/success",
            cancel_url=config.PUBLIC_BASE_URL + "/payment/cancel",
        )
        db.execute("INSERT INTO checkouts VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 0)", (
            session.id, user_id, chat_id, config.SUBSCRIPTION_PRICE_PENCE,
            config.SUBSCRIPTION_CURRENCY.lower(), config.SUBSCRIPTION_DURATION_DAYS,
            session.url, session.expires_at,
        ))
        return session.url


def approve(user_id, chat_id):
    member = get_chat_member(chat_id, user_id)
    if member.get("status") in {"creator", "administrator", "member"}:
        return
    if member.get("status") == "restricted" and member.get("is_member"):
        return
    approve_chat_join_request(chat_id, user_id)


def approve_if_paid(user_id, chat_id):
    with database() as db:
        row = db.execute(
            "SELECT 1 FROM checkouts WHERE user_id=? AND chat_id=? AND paid_until>?",
            (user_id, chat_id, int(time.time())),
        ).fetchone()
    if row:
        approve(user_id, chat_id)
        return True
    return False


def fulfill(session):
    if session.get("payment_status") != "paid" or session.get("mode") != "payment":
        return
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM checkouts WHERE session_id=?", (session["id"],)).fetchone()
        if not row or row["fulfilled"]:
            return
        metadata = session.get("metadata") or {}
        if (session.get("amount_total") != row["amount"]
                or session.get("currency") != row["currency"]
                or session.get("client_reference_id") != str(row["user_id"])
                or metadata.get("telegram_user_id") != str(row["user_id"])
                or metadata.get("telegram_chat_id") != str(row["chat_id"])):
            raise ValueError("Checkout does not match the stored payment")
        if row["paid_until"] is None:
            db.execute("UPDATE checkouts SET paid_until=? WHERE session_id=?", (
                int(time.time()) + row["duration"] * 86400, session["id"],
            ))
        # Persist payment before Telegram: an API failure must not lose payment.
        db.commit()
        db.execute("BEGIN IMMEDIATE")
        current = db.execute("SELECT fulfilled FROM checkouts WHERE session_id=?", (session["id"],)).fetchone()
        if current["fulfilled"]:
            return
        approve(row["user_id"], row["chat_id"])
        db.execute("UPDATE checkouts SET fulfilled=1 WHERE session_id=?", (session["id"],))
