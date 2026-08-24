Perfect 👍 — connecting **AWS → GitHub** is the **correct enterprise workflow**.

After this, you will deploy like real companies:

```
Code → GitHub → AWS Server → Auto Update
```

I’ll give you **clean STEP-BY-STEP**.

---

# 🚀 METHOD 1 — Connect AWS EC2 to GitHub (Recommended)

You will make your AWS server pull code directly from GitHub.

---

## ✅ Step 1 — Install Git on AWS

SSH into EC2:

```bash
ssh ubuntu@YOUR_PUBLIC_IP
```

Install git:

```bash
sudo apt update
sudo apt install git -y
```

Check:

```bash
git --version
```

---

## ✅ Step 2 — Create SSH Key on AWS

Generate key:

```bash
ssh-keygen -t ed25519 -C "aws-server"
```

Press ENTER for everything.

Keys created:

```
~/.ssh/id_ed25519
~/.ssh/id_ed25519.pub
```

---

## ✅ Step 3 — Copy Public Key

Show key:

```bash
cat ~/.ssh/id_ed25519.pub
```

Copy the entire output.

---

## ✅ Step 4 — Add Key to GitHub

Go to:

👉 **GitHub**

### Open:

```
Settings
→ SSH and GPG keys
→ New SSH key
```

Paste the key.

Save.

---

## ✅ Step 5 — Test GitHub Connection

On AWS:

```bash
ssh -T git@github.com
```

You should see:

```
Hi username! You've successfully authenticated.
```

✅ Connected.

---

## ✅ Step 6 — Clone Repository

Go to home:

```bash
cd ~
```

Clone repo:

```bash
git clone git@github.com:USERNAME/REPO.git
```

Example:

```bash
git clone git@github.com:saurabh/amazon-job-bot.git
```

---

## ✅ Step 7 — Enter Project

```bash
cd amazon-job-bot
```

---

## ✅ Step 8 — Setup Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## ✅ Step 9 — Run Production Service

Restart service:

```bash
sudo systemctl restart amazonbot
```

---

# 🔥 DAILY WORKFLOW (SUPER IMPORTANT)

Now deployment becomes:

### 1️⃣ Change code on laptop

### 2️⃣ Push to GitHub

```bash
git add .
git commit -m "update"
git push
```

### 3️⃣ On AWS server

```bash
git pull
sudo systemctl restart amazonbot
```

✅ New version live.

---

# 🚀 METHOD 2 — AUTO DEPLOY (REAL ENTERPRISE)

We can make AWS automatically update when you push to GitHub.

This is called:

✅ **CI/CD pipeline**

Uses:

* GitHub Actions
* auto deploy
* zero manual SSH

If you want, I’ll build:

✅ Push code → AWS updates automatically
✅ Bot restarts itself
✅ Zero downtime deploy
✅ Production DevOps setup

Just say:

👉 **“setup auto deploy”** 🔥

http://3.10.144.29
http://3.10.144.29:8000/

✅ Enterprise Amazon Bot Running


sudo ss -tulpn | grep 8000


tcp   LISTEN 0      4096              0.0.0.0:8000      0.0.0.0:*    users:(("docker-proxy",pid=163192,fd=8))
tcp   LISTEN 0      4096                 [::]:8000         [::]:*    users:(("docker-proxy",pid=163198,fd=8))


sudo ss -tulpn | grep 8000

curl localhost:8000

else

do 
this


printenv | grep TELEGRAM

if empty

fix

sudo nano /etc/systemd/system/amazonbot.service

add

[Unit]
Description=Amazon Job Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/job-aws-bot
Environment="TELEGRAM_BOT_TOKEN=YOUR_NEW_TOKEN"
Environment="TELEGRAM_CHAT_IDS=7943617436"
ExecStart=/home/ubuntu/job-aws-bot/venv/bin/gunicorn -w 2 -b 0.0.0.0:8001 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target

sudo systemctl daemon-reload
sudo systemctl restart amazonbot
sudo systemctl status amazonbot

http://3.10.144.29:8000/

✅ Enterprise Amazon Bot Running


post to github from aws ec2

From your **AWS EC2 terminal**, run this inside your project folder:

```bash
cd ~/job-aws-bot
git status
```

If it is **not already connected to GitHub**:

```bash
git init
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

Then push your code:

```bash
git add .
git commit -m "Update bot code"
git branch -M main
git push -u origin main
```

If GitHub asks for a password, use a **GitHub Personal Access Token**, not your GitHub password.

To avoid uploading secrets, first create `.gitignore`:

```bash
nano .gitignore
```

Add:

```bash
venv/
.env
__pycache__/
*.pyc
```

Then save and push again:

```bash
git add .gitignore
git add .
git commit -m "Initial EC2 bot upload"
git push -u origin main
```

Important: do **not** push your Telegram bot token to GitHub.


