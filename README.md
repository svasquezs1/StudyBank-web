# StudyBank

> A collaborative web platform where university students share study materials and book tutoring sessions.

StudyBank is a Django-based web application that helps university students overcome the lack of study resources and academic support. It works as a collaborative repository where students can upload, search, filter, view the details of, and download study materials by course. It also connects students with tutors: users can register as tutors indicating the subjects they offer, and other students can search for tutors by subject.

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

Institutional accounts, study material sharing (upload, search, filter, view, download), and a tutoring directory (tutor registration and search by subject) are implemented as of Sprint 1. Ratings, tutoring requests, and notifications are planned for upcoming sprints.

See the full, detailed list of requirements — implemented and planned — in the [Requirements Prioritisation](../../wiki/Requirements-Prioritisation) wiki page.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python + Django (MVT) |
| Database | SQLite |
| File storage | Cloudflare R2 (S3-compatible) |
| Static files | WhiteNoise |
| Deployment | PythonAnywhere |
| Version control | Git + GitHub |

---

## 👥 Team

| Name | Role | GitHub | Email |
|------|------|--------|-------|
| Sebastián Vásquez | Backend — Accounts & Materials | [@svasquezs1](https://github.com/svasquezs1) | svasquezs1@eafit.edu.co |
| Gisel Jaramillo | Backend — Materials | [@gljaramilloc](https://github.com/gljaramilloc) | gljaramilc@eafit.edu.co |
| Samuel Serna | Backend — Tutoring | [@sserna12](https://github.com/sserna12) | sserna@eafit.edu.co |

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
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Windows
   copy .env.example .env

   # macOS / Linux
   cp .env.example .env
   ```
   Then open `.env` and fill in the values. Generate a `SECRET_KEY` with:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

5. **Apply migrations and create a superuser**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```
   You will be prompted for an email (not a username), since accounts log in with their institutional email.

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000` in your browser.

---

## 📁 Project Structure

```
StudyBank-web/
├── config/          # Project settings, main URLs, WSGI
├── accounts/        # Users, profiles, authentication
├── materials/       # Study materials, filters, search
├── tutoring/        # Tutors, subjects, search
├── templates/       # Shared HTML templates
├── static/          # CSS, JS, images
├── manage.py
├── requirements.txt
└── .env.example
```

---

## 🌐 Deployment

The application will be deployed on **PythonAnywhere**, with user-uploaded files stored on **Cloudflare R2**. Deployment is planned for a later sprint; a live demo link will be added here once available.

See the deployment guide in the [Wiki](#-documentation) for full setup instructions.

---

## 📖 Documentation

Full project documentation lives in the **[GitHub Wiki](../../wiki)**:
- Product vision and problem statement
- Requirements specification and prioritisation
- Domain model
- High-level design and deployment model
- Meeting minutes

Project management (backlog and Kanban board) is tracked in **[GitHub Projects](../../projects)**.

---

## 📄 License

This project was developed for academic purposes as part of the Proyecto Integrador 1 course at Universidad EAFIT.
