# StudyBank
 
> A collaborative web platform where university students share study materials and connect with tutors.
 
StudyBank is a Django-based web application designed for the Universidad EAFIT student community. Its purpose is to reduce the time students spend searching for academic resources and support by centralizing study materials and tutoring services in one platform.
 
Students can use StudyBank to access academic resources and find tutors according to the subjects in which they need support.
 
---
 
## 📚 Table of Contents
 
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Team](#-team)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [Deployment](#-deployment)
- [Documentation](#-documentation)
---
 
## ✨ Features
 
### Current MVP
 
The current MVP includes the following functionality:
 
- Institutional user registration, login, and logout.
- Profile editing (name, university, program, and profile picture).
- University and academic program management.
- Study material upload, keyword search, filtering by course, detail view, and download.
- Tutor registration with subject selection.
- Administrative approval of tutor profiles.
- Tutor search by subject.
- Tutoring session requests, specifying subject, date, time, and mode (in person or virtual).
- Acceptance or rejection of tutoring requests by tutors.
- Material ratings (1 to 5 stars, after downloading) and catalog sorting by rating or downloads.
- Tutor availability (recurring weekly time slots).
- Tutor public profile with average rating.
- Completion and rating of tutoring sessions, and tutor sorting by rating.
- In-app notifications when a tutoring request is created, accepted or rejected.
- Shared and responsive visual interface, with a mobile menu.
### Planned functionality
 
Sprint 4 (in progress) adds the public user profile (RF-23), editing and deleting uploaded materials (RF-24, RF-25), filtering materials by university (RF-26), cancelling tutoring sessions (RF-28), tutor activity statistics (RF-30) and the production deployment on AWS EC2. Password recovery (RF-22) remains in the backlog.
 
The complete list of functional requirements, their priorities, and their current status is documented in the project Wiki.
 
See:
 
- [Requirements Specification](https://github.com/svasquezs1/StudyBank-web/wiki/Deliverable-1#2-specific-requirements)
- [Requirements status, sprint, and responsible person](https://github.com/svasquezs1/StudyBank-web/wiki/Requirements)
---
 
## 🛠️ Tech Stack
 
| Layer | Technology |
|-------|------------|
| Backend | Python 3.12 + Django 6.0.7 (MVT) |
| Database | SQLite 3 |
| Production server | AWS EC2 — Amazon Linux 2023 |
| Static files | WhiteNoise |
| Uploaded files | Server disk (`media/`); Cloudflare R2 (S3-compatible) optional |
| Version control | Git + GitHub |
| Project management | GitHub Projects |
| Documentation | GitHub Wiki |
 
---
 
## 👥 Team
 
| Name | Role | GitHub | Email |
|------|------|--------|-------|
| Sebastián Vásquez Saldarriaga | Backend — Accounts & Materials | [@svasquezs1](https://github.com/svasquezs1) | svasquezs1@eafit.edu.co |
| Gisel Lorena Jaramillo Carmona | Backend — Materials | [@gljaramilloc](https://github.com/gljaramilloc) | gljaramilc@eafit.edu.co |
| Samuel Serna Patiño | Backend — Tutoring | [@sserna12](https://github.com/sserna12) | sserna@eafit.edu.co |
 
**Course:** Proyecto Integrador 1 (ST0251) — Universidad EAFIT
**Professor:** Mario Andrés Jaramillo
 
---
 
## 🚀 Getting Started
 
### Prerequisites
 
- Python 3.12 or higher
- Git
### Installation
 
1. **Clone the repository**
```bash
   git clone https://github.com/svasquezs1/StudyBank-web.git
   cd StudyBank-web
```
 
2. **Create and activate a virtual environment**
   **Windows**
```bash
   python -m venv venv
   venv\Scripts\activate
```
 
   **macOS / Linux**
 
```bash
   python3 -m venv venv
   source venv/bin/activate
```
 
3. **Install dependencies**
```bash
   pip install -r requirements.txt
```
 
4. **Configure environment variables**
   If an `.env.example` file is available, create a local `.env` file from it.
   **Windows**
```bash
   copy .env.example .env
```
 
   **macOS / Linux**
 
```bash
   cp .env.example .env
```
 
   Generate a Django `SECRET_KEY` with:
 
```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
 
   Environment-specific values such as `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` must not be committed with production secrets.
 
5. **Apply migrations**
```bash
   python manage.py migrate
```
 
6. **Load the shared starting data**
```bash
   python manage.py seed_studybank
```
 
   This creates the shared catalogs (Universidad EAFIT, its programs, the courses and the tutoring subjects) and the team administrator accounts `sebastian@eafit.edu.co`, `gisel@eafit.edu.co` and `samuel@eafit.edu.co`, so every member works with the same data. Their password is read from `SEED_ADMIN_PASSWORD` in your `.env`; the team shares the value privately and it is never committed. The command can be run again at any time without duplicating anything; add `--reset-admin-passwords` to set the administrators' password to the current value of `SEED_ADMIN_PASSWORD`.
 
   StudyBank uses email-based authentication, so accounts are identified by their email address rather than a traditional username. To start again from a clean database, delete `db.sqlite3` and repeat steps 5 and 6.
 
7. **Run the development server**
```bash
   python manage.py runserver
```
 
   Open:
 
   `http://127.0.0.1:8000`
 
8. **Run the automated tests**
```bash
   python manage.py test
```
 
---
 
## 📁 Project Structure
 
```text
StudyBank-web/
├── config/          # Django project configuration
├── accounts/        # Users, authentication, universities and programs
├── materials/       # Study materials, downloads and material ratings
├── tutoring/        # Tutors, subjects, availability, tutoring requests and ratings
├── notifications/   # In-app notifications for tutoring requests
├── templates/       # Shared HTML templates
├── static/          # CSS, JavaScript and images
├── manage.py
├── requirements.txt
└── .env.example
```
 
---
 
## 🌐 Deployment
 
StudyBank is deployed on an **AWS EC2** instance (`t3.micro`, **Amazon Linux 2023**) of the **AWS Academy Learner Lab**, following the course tutorial *Taller 4 — Despliegue: AWS + Django*:
 
- The Django server runs on port 80 inside a **Python 3.12** virtual environment, with `DEBUG=False`.
- **WhiteNoise** serves the static files, **SQLite** stores the data and uploaded files are kept in `media/` on the instance.
- The public IP changes every time the Learner Lab starts, so [`deploy/start_studybank.sh`](deploy/start_studybank.sh) writes the current IP into `.env` and starts the server.
The step-by-step guide (Learner Lab, instance, production `.env`, start, update and troubleshooting) is in [`deploy/README.md`](deploy/README.md).
 
**Live application:** the address is printed by `deploy/start_studybank.sh` each time the lab starts (for example `http://3.94.193.168`).
 
---
 
## 📖 Documentation
 
The complete project documentation is maintained in the **[GitHub Wiki](https://github.com/svasquezs1/StudyBank-web/wiki)**.
 
The Wiki contains:
 
- [Deliverable 1](https://github.com/svasquezs1/StudyBank-web/wiki/Deliverable-1) — project definition and Software Requirements Specification.
- [Deliverable 2](https://github.com/svasquezs1/StudyBank-web/wiki/Deliverable-2) — solution design and functionality preview.
- [Deliverable 3](https://github.com/svasquezs1/StudyBank-web/wiki/Deliverable-3) — MVP.
- [Requirements](https://github.com/svasquezs1/StudyBank-web/wiki/Requirements) — status, sprint, and responsible person for every requirement.
- [Weekly Meetings](https://github.com/svasquezs1/StudyBank-web/wiki/Weekly-Meetings)
- [Retrospectives](https://github.com/svasquezs1/StudyBank-web/wiki/Retrospectives)
- [Classwork](https://github.com/svasquezs1/StudyBank-web/wiki/Classwork)
Project requirements, backlog, progress, and task tracking are managed through the **[StudyBank Project Board](https://github.com/users/svasquezs1/projects/2)**.
 
---
 
## 📄 Academic Use
 
StudyBank is being developed for academic purposes as part of the course **Proyecto Integrador 1 (ST0251)** at Universidad EAFIT.
