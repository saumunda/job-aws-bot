# Telegram group payments with Stripe

This standalone Flask service creates a private Stripe Checkout link when someone
requests to join your group. A verified Stripe webhook approves that exact Telegram
user after payment. The existing default is a **one-time GBP 1.00 payment**.

Stripe Projects (https://docs.stripe.com/projects) provisions infrastructure. This
integration uses Checkout Sessions (https://docs.stripe.com/api/checkout/sessions/create)
and signed payment webhooks (https://docs.stripe.com/webhooks).

## Setup

1. Rotate the Telegram bot token previously stored in `.env.example` using BotFather.
2. Use a **private group with approval-required invite links**. Revoke old direct-join
   links and avoid manually approving unpaid users. Public groups/direct invites
   bypass the payment gate. Give the bot administrator permission `can_invite_users`.
3. Export the variables in `.env.example` into the service environment. The example
   file is a template and is not loaded automatically. Use your numeric group ID.
   `PUBLIC_BASE_URL` must be the HTTPS address of this Flask service, not a t.me URL.
4. Obtain a Stripe test secret key (`sk_test_...`). A publishable `pk_...` key cannot
   create Checkout Sessions. Set `STRIPE_SECRET_KEY`.
5. Register `https://YOUR_DOMAIN/stripe/webhook` in Stripe for
   `checkout.session.completed` and `checkout.session.async_payment_succeeded`.
   Set its signing secret (`whsec_...`) as `STRIPE_WEBHOOK_SECRET`.
6. Set `WEBHOOK_SECRET_TOKEN` to a separate random secret for Telegram.
7. Install and start from this directory:

```powershell
pip install -r requirements.txt
python app.py
```

For Linux production, run `gunicorn --workers 2 --bind 0.0.0.0:8010 wsgi:app`
behind HTTPS. Deploy this service alongside the root job-alert application: the
root `app.py` does not serve these payment routes. Only one Telegram webhook can
be registered per bot; route all needed updates here or use a separate payment bot.

8. Set `WEBHOOK_URL=https://YOUR_DOMAIN/telegram/webhook`, then run
   `python set_webhook.py` to register Telegram updates.
9. Start the bot in Telegram, request to join using the approval-required link,
   and complete a test Checkout. Confirm that only the paying account is approved.
   After testing, configure the live Stripe key and live endpoint signing secret.

## Payment behavior and operations

- Checkout sessions are bound server-side to user ID, group ID, amount and currency.
- Only signed events with `payment_status=paid` grant access. Redirect pages do not.
- SQLite records payments, suppresses duplicate fulfillment, and preserves payment
  when Telegram approval fails. A failed delivery returns HTTP 500 for Stripe retry.
- If approval failed because a request was withdrawn, request to join again. A
  recorded payment within its configured duration allows rejoining without payment.
- Pending Checkout links are reused until near expiry. Unpaid/cancelled requests
  remain pending. The bot does not automatically decline or approve them.
- Telegram's temporary join-request DM permission lasts about five minutes and may
  be unavailable; start the bot first and submit a fresh join request if needed.
- `SUBSCRIPTION_DURATION_DAYS` defaults to 365 and controls paid rejoin eligibility.
  **Automatic expiry removal, recurring billing, refunds and dispute revocation are
  not implemented.** Group members remain until removed by an administrator.
- Keep `PAYMENTS_DB` on persistent local storage and back it up. All workers must
  share this database. Multiple hosts require a shared transactional database.
- Stripe mode disables generic public payment reminders and post-join payment
  prompts. An approval must not generate another charge prompt.
- With no `STRIPE_SECRET_KEY`, the legacy `PAYMENT_LINK` flow remains available;
  payments in that mode require manual verification and approval.

## Verification

```powershell
python -m unittest discover -p "test_*.py"
```

Tests mock external API calls and use genuine Stripe webhook signatures. They cover
identity/amount checks, delayed payments, duplicate events, approval retries,
paid rejoining, and signature rejection. Live Stripe/Telegram testing is still
required with your credentials and deployed HTTPS address.
