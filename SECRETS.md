# Secret Handling

The Telegram token was previously hard-coded in `amazonbot.service`. Treat that
token as exposed: revoke it with BotFather and create a replacement before
starting the updated service.

## Local Development

Copy `.env.example` to `.env` and put the replacement token and chat IDs in
`.env`. `config.py` loads this file with `python-dotenv`. `.env` is ignored by
Git; `.env.example` contains no credentials.

This checkout is under OneDrive. Windows file permissions protect it from other
local Windows accounts, but OneDrive sharing permissions still control who can
see synced files. Do not put a production token in this checkout if the OneDrive
folder is shared.

To restrict a local `.env` file to your Windows account, run PowerShell in the
repository directory:

```powershell
$account = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
icacls .env /inheritance:r
icacls .env /grant:r "$($account):(F)" "SYSTEM:(F)" "Administrators:(F)"
icacls .env
```

## Amazon EC2

Keep the production environment file outside the Git checkout. The systemd unit
loads `/etc/job-aws-bot/amazonbot.env`:

```bash
sudo install -d -o root -g root -m 700 /etc/job-aws-bot
sudo touch /etc/job-aws-bot/amazonbot.env
sudo chown root:root /etc/job-aws-bot/amazonbot.env
sudo chmod 600 /etc/job-aws-bot/amazonbot.env
sudoedit /etc/job-aws-bot/amazonbot.env
```

Enter these values in the editor, using the replacement token from BotFather:

```dotenv
TELEGRAM_BOT_TOKEN=replace_with_new_token
TELEGRAM_CHAT_IDS=your_group_chat_id
```

Then install the secret-free unit, reload systemd, and restart the service:

```bash
sudo install -o root -g root -m 644 /home/ubuntu/job-aws-bot/amazonbot.service /etc/systemd/system/amazonbot.service
sudo systemctl daemon-reload
sudo systemctl restart amazonbot
sudo stat -c '%U:%G %a %n' /etc/job-aws-bot /etc/job-aws-bot/amazonbot.env
```

The directory should be `root:root` mode `700`; the environment file should be
`root:root` mode `600`. Do not print the environment file or use commands that
dump the service environment to logs.

## GitHub

Commit application code and `.env.example` only. Never commit `.env`, paste the
token into an issue, or print it in a GitHub Actions log. No Actions workflow is
currently configured in this repository, so the EC2 service reads its secret
directly from the protected file. If a deployment workflow is added later, use
GitHub Actions secrets only for values that workflow needs, and grant the EC2
instance role access only to the specific AWS secret it must retrieve. See
[GitHub Actions secrets](https://docs.github.com/en/actions/concepts/security/secrets)
and [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html).
