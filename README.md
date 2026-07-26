# StudyBank

> A collaborative web platform where university students share study materials and book tutoring sessions.

StudyBank is a Django-based web application that helps university students overcome the lack of study resources and academic support. It works as a collaborative repository where students can upload, search, filter, download, and rate study materials by course and professor. It also connects students with tutors: users can register as tutors, set their availability, and receive session requests, while students can browse tutors and book in-person or virtual sessions.

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

- **Study materials**: upload PDFs, search and filter by university, program, course, professor, type, and semester.
- **Ratings**: rate materials so the best resources stand out.
- **Tutoring**: register as a tutor, set availability, and receive booking requests.
- **Booking**: browse tutors and book in-person or virtual sessions.
- **Institutional access**: registration restricted to `@eafit.edu.co` email addresses.
- **User profiles**: personal profile showing uploaded materials and account options.

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
| [Gisel Lorena] | [] | [@gljaramilloc] | [gljaramilc@eafit.edu.co] |
| [Samuel Serna] | [] | [@sserna12] | [sserna@eafit.edu.co] |
| [Sebastian Vasquez] | [] | [@svasquezs1] | [svasquezs1@eafit.edu.co] |


**Course:** Proyecto Integrador 1 (ST0251) — Universidad EAFIT
**Professor:** [Mario Andres Jaramillo]

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher
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
├── materials/       # Study materials, filters, ratings
├── tutoring/        # Tutors, availability, bookings
├── templates/       # Shared HTML templates
├── static/          # CSS, JS, images
├── manage.py
├── requirements.txt
└── .env.example
```

---

## 🌐 Deployment

The application is deployed on **PythonAnywhere**, with user-uploaded files stored on **Cloudflare R2**.

<!-- Cuando esté desplegado, agrega el enlace: -->
**Live demo:** [https://TU_USUARIO.pythonanywhere.com](#)

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