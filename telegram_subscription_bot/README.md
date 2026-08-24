# Telegram Subscription Bot

This is a standalone bot for asking new Telegram channel or group members to pay
GBP 1.00 for a one-year subscription.

It listens for:

- `chat_join_request`: best for private channels/groups that require approval.
  Telegram gives the bot a temporary private `user_chat_id`, so the bot can send
  the payment prompt directly to the requester.
- `chat_member`: useful after a user joins. Telegram only allows a DM here if the
  user has already started the bot.
- `successful_payment`: records the paid subscription and optionally approves a
  pending join request.

The bot never posts the payment prompt publicly in the group/channel.

## Setup

1. Create a Telegram bot with `@BotFather`.
2. Add the bot as an admin in your channel/group.
3. If you want the best private-payment flow, enable join requests for the invite
   link and give the bot the `can_invite_users` admin permission.
4. Copy `.env.example` values into your server environment.
5. Install and run:

```powershell
pip install -r requirements.txt
python app.py
```

## Environment

Required:

- `TELEGRAM_BOT_TOKEN`: token from `@BotFather`
- `CHANNEL_CHAT_ID`: your channel/group id, for example `-1001234567890`, or a
  public username like `@mychannel`

Payment options:

- Set `TELEGRAM_PROVIDER_TOKEN` to send a Telegram invoice for GBP 1.00.
- Or set `PAYMENT_LINK` to send a private payment-link button.

Optional:

- `WEBHOOK_SECRET_TOKEN`: Telegram webhook secret header.
- `APPROVE_JOIN_REQUESTS_AFTER_PAYMENT`: defaults to `1`.
- `SUBSCRIPTION_PRICE_PENCE`: defaults to `100`.
- `SUBSCRIPTION_DURATION_DAYS`: defaults to `365`.
- `SUBSCRIPTION_DATA_FILE`: defaults to `data/subscribers.json`.

## Webhook

Expose this app over HTTPS, then set the webhook:

```powershell
$body = @{
  url = "https://YOUR_DOMAIN/telegram/webhook"
  secret_token = $env:WEBHOOK_SECRET_TOKEN
  allowed_updates = @("chat_join_request", "chat_member", "message", "pre_checkout_query")
  drop_pending_updates = $true
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "https://api.telegram.org/bot$env:TELEGRAM_BOT_TOKEN/setWebhook" `
  -ContentType "application/json" `
  -Body $body
```

## Important Telegram Limit

For `chat_member` join events, Telegram blocks bots from starting a new private
DM unless the member has already opened the bot and pressed Start. For
`chat_join_request`, Telegram provides `user_chat_id`, which lets the bot message
the requester privately for a short window while the request is pending.