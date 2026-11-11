# Deploying StudyBank on AWS EC2

StudyBank is deployed on an **AWS EC2** instance of the **AWS Academy Learner Lab**, following the course tutorial *Taller 4 — Despliegue: AWS + Django*.

```text
Browser ──HTTP :80──▶ EC2 instance (Amazon Linux 2023)
                       └── Python 3.12 virtual environment
                            └── Django 6.0.7 server (manage.py runserver 0.0.0.0:80)
                                 ├── WhiteNoise → staticfiles/ (CSS, JS, images)
                                 ├── media/ (uploaded materials and profile pictures)
                                 └── SQLite 3 (db.sqlite3)
```

| Component | Version | Role |
|---|---|---|
| AWS EC2 | `t3.micro` | Virtual server of the Learner Lab (region `us-east-1`) |
| Amazon Linux 2023 | AL2023 | Operating system |
| Python | 3.12 (virtual environment `venv/`) | Runtime; Django 6 requires Python 3.12 or higher |
| Django | 6.0.7 | Web framework and server on port 80 |
| WhiteNoise | 6.12.0 | Serves the collected static files with `DEBUG=False` |
| SQLite | 3 | Relational database |

Files in this folder:

| File | Purpose |
|---|---|
| `start_studybank.sh` | Writes the current public IP into `.env` and starts the server on port 80 |
| `update.sh` | Deploys the latest version of `main` and restarts the server |

---

## 1. Start the Learner Lab

1. Open AWS Academy → course *AWS Academy Learner Lab* → **Modules** → **Launch AWS Academy Learner Lab**.
2. Click **Start Lab** and wait until the AWS indicator is green.
3. Click **AWS** to open the console and go to **EC2 → Instances**.
## 2. Create the instance (first time only)

**EC2 → Launch instance**:

1. **Name:** `studybank-web`.
2. **AMI:** Amazon Linux 2023.
3. **Instance type:** `t3.micro`.
4. **Key pair:** *Proceed without a key pair* — the connection is made with EC2 Instance Connect.
5. **Network settings:** allow SSH, HTTP and HTTPS traffic from the internet.
6. **Launch instance**.
## 3. Connect to the instance

Select the instance → **Connect** → **EC2 Instance Connect** → **Connect**. A terminal opens in the browser as `ec2-user`.

## 4. Install and configure the project (first time only)

```bash
sudo dnf install python3.12 python3.12-pip git -y

cd ~
git clone https://github.com/svasquezs1/StudyBank-web.git
cd StudyBank-web

python3.12 -m venv venv
venv/bin/python -m pip install -r requirements.txt
```

Create the production `.env`:

```bash
cp .env.example .env
python3.12 -c "import secrets; print(secrets.token_urlsafe(50))"   # copy the result
nano .env
```

```dotenv
SECRET_KEY=<the value generated above>
DEBUG=False
ALLOWED_HOSTS=
CSRF_TRUSTED_ORIGINS=
SERVE_MEDIA=True
SEED_ADMIN_PASSWORD=<the administrators' password shared by the team>
```

`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are filled in automatically by `start_studybank.sh`. `SERVE_MEDIA=True` lets Django serve the uploaded files while `DEBUG=False`. Leave the `R2_*` variables empty.

Prepare the database and the static files, and load the shared catalogs and the team administrator accounts:

```bash
sudo venv/bin/python manage.py migrate
sudo venv/bin/python manage.py collectstatic --noinput
sudo venv/bin/python manage.py seed_studybank
```

On an instance that already has data, only run `seed_studybank` (never delete `db.sqlite3` there): it adds what is missing and keeps the existing users, materials and requests.

## 5. Start the server

```bash
bash ~/StudyBank-web/deploy/start_studybank.sh
```

The script prints the address, for example `StudyBank corriendo en: http://3.94.193.168`. Open it in the browser.

**Every time the lab is started again**, the instance gets a new public IP: start the instance if it is stopped, connect with EC2 Instance Connect and run `start_studybank.sh` again.

## 6. Deploy a new version

After merging changes into `main`:

```bash
bash ~/StudyBank-web/deploy/update.sh
```

It pulls `main`, installs the dependencies, applies the migrations, collects the static files and restarts the server.

## 7. Stop the instance

To save the lab budget: **EC2 → Instances → Instance state → Stop instance**, then **End Lab** in the Learner Lab.

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| The page does not load | The server is not running or the IP changed | Run `start_studybank.sh` and use the address it prints |
| `Bad Request (400)` | The IP is not in `ALLOWED_HOSTS` | Run `start_studybank.sh` again |
| `403 CSRF verification failed` on forms | `CSRF_TRUSTED_ORIGINS` does not have the current IP | Run `start_studybank.sh` again |
| Page without styles | Static files were not collected | `sudo venv/bin/python manage.py collectstatic --noinput` |
| Uploaded files or profile pictures return 404 | `SERVE_MEDIA` is not `True` | Set `SERVE_MEDIA=True` in `.env` and run `start_studybank.sh` |
| `Error: That port is already in use` | A previous server is still running | `sudo pkill -f "manage.py runserver"` and start again |

Server log: `tail -n 50 ~/StudyBank-web/server.log`
