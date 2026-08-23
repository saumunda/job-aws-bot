#!/bin/bash
set -e

cd /home/ubuntu/job-aws-bot

echo "Pulling latest code..."
git fetch origin
git reset --hard origin/main

echo "Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "Restarting service..."
sudo systemctl restart amazonbot

echo "Done."
