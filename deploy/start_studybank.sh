#!/bin/bash
# Starts StudyBank on the AWS EC2 instance (Amazon Linux 2023).
#
# The public IP of the instance changes every time the AWS Academy Learner Lab
# starts, so this script:
#   1. reads the current public IP from the instance metadata,
#   2. writes it into ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS in .env,
#   3. restarts the Django server on port 80 in the background.
#
# Usage (as ec2-user, after every lab start):
#   bash ~/StudyBank-web/deploy/start_studybank.sh
# The server output is written to ~/StudyBank-web/server.log
cd ~/StudyBank-web || exit 1

if [ ! -f .env ]; then
    echo "Missing .env file. Create it from .env.example (see deploy/README.md)."
    exit 1
fi

TOKEN=$(curl -s -X PUT http://169.254.169.254/latest/api/token -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4)

if [ -z "$IP" ]; then
    echo "Could not read the public IP of the instance."
    exit 1
fi

sed -i "s|^ALLOWED_HOSTS=.*|ALLOWED_HOSTS=$IP|; s|^CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=http://$IP|" .env

sudo pkill -f "manage.py runserver"
sudo nohup venv/bin/python manage.py runserver 0.0.0.0:80 > server.log 2>&1 &

echo "StudyBank corriendo en: http://$IP"
