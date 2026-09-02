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

The current MVP includes core functionality such as:

- Institutional user registration and authentication.
- University and academic program management.
- Study material upload, detail view, and download.
- Tutor registration.
- Subject selection for tutors.
- Administrative approval of tutor profiles.
- Tutor search by subject.
- Shared and responsive visual interface.

### Planned functionality

Additional functionality is being developed and prioritised through the project backlog and requirements specification.

This includes features related to:

- Study material search and filtering.
- Material ratings.
- Tutor availability.
- Tutoring requests.
- Acceptance or rejection of tutoring requests.
- Notifications.
- Additional tutoring and material management capabilities defined in the backlog.

The complete list of functional requirements, their priorities, and their current status is documented in the project Wiki.

See:

- [Requirements Specification](https://github.com/svasquezs1/StudyBank-web/wiki/Requirements-Specification)
- [Requirements Prioritisation](https://github.com/svasquezs1/StudyBank-web/wiki/Requirements-Prioritisation)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python + Django (MVT) |
| Database | SQLite |
| Production file storage | Cloudflare R2 (S3-compatible) — planned/configurable |
| Static files | WhiteNoise |
| Production deployment | PythonAnywhere — planned |
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

6. **Create a superuser if administrative access is required**

   ```bash
   python manage.py createsuperuser
   ```

   StudyBank uses email-based authentication, so the account is associated with an email address rather than a traditional username.

7. **Run the development server**

   ```bash
   python manage.py runserver
   ```

   Open:

   `http://127.0.0.1:8000`

---

## 📁 Project Structure

```text
StudyBank-web/
├── config/          # Django project configuration
├── accounts/        # Users, authentication, universities and programs
├── materials/       # Study materials module
├── tutoring/        # Tutors, subjects and tutor search
├── templates/       # Shared HTML templates
├── static/          # CSS, JavaScript and images
├── manage.py
├── requirements.txt
└── .env.example
```

---

## 🌐 Deployment

The application is currently under development.

The planned production environment uses **PythonAnywhere** for deployment and **Cloudflare R2** for user-uploaded file storage.

These services should not be interpreted as the current production state until the final deployment has been completed and validated.

A live application link will be added once deployment is available.

---

## 📖 Documentation

The complete project documentation is maintained in the **[GitHub Wiki](https://github.com/svasquezs1/StudyBank-web/wiki)**.

The Wiki contains:

- Project overview.
- Product Vision Board.
- Requirements specification.
- Requirements prioritisation.
- Domain model.
- Architecture and diagrams.
- Team information.
- Meeting minutes.

Project requirements, backlog, progress, and task tracking are managed through the **[StudyBank Project Board](https://github.com/users/svasquezs1/projects/2)**.

---

## 📄 Academic Use

StudyBank is being developed for academic purposes as part of the course **Proyecto Integrador 1 (ST0251)** at Universidad EAFIT.
