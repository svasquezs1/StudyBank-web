#!/bin/bash
# Deploys the latest version of main on the AWS EC2 instance.
#
# Usage (as ec2-user):
#   bash ~/StudyBank-web/deploy/update.sh
set -e
cd ~/StudyBank-web

echo "==> Pulling the latest code from main"
git checkout main
git pull origin main

echo "==> Installing dependencies"
venv/bin/python -m pip install -r requirements.txt

echo "==> Applying migrations and collecting static files"
# The server runs as root (port 80), so the database and static files are
# updated with the same user.
sudo venv/bin/python manage.py migrate --noinput
sudo venv/bin/python manage.py collectstatic --noinput

echo "==> Restarting the server"
bash deploy/start_studybank.sh
