#!/bin/bash
set -e

cd /home/ubuntu/job-aws-bot

git fetch origin
git reset --hard origin/main

source venv/bin/activate
pip install -r requirements.txt

sudo systemctl restart amazonbot
