# Online Quiz System with Performance Analytics

A production-style REST API based quiz platform built with **FastAPI** and **PostgreSQL**.

## Features
- **User Authentication**: Secure Registration & Login (JWT + Hashing) for Students & Teachers.
- **Quiz Management**: Teachers can create quizzes with multiple options and difficulty levels.
- **Quiz Attempt**: Students can take quizzes with real-time timers.
- **Performance Analytics**: Average scores, Leaderboards, and Toughest Questions tracking.
- **Modern UI**: Dark-mode glassmorphic interface.

---

## Tech Stack
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL via `psycopg2-binary`
- **Frontend**: HTML5, CSS3 (Glassmorphism), Vanilla JavaScript (Fetch API)
- **Deployment**: Render (Web Service & Managed PostgreSQL)

---

## Getting Started

### 1. Prerequisites
- **Python 3.8+**
- **PostgreSQL Database** (Local or Managed Cloud like Render)

### 2. Database Setup
The application includes a setup script that will automatically initialize your database schema.
You will need an empty PostgreSQL database ready to connect to.

### 3. Installation
Clone or navigate to the project directory and install dependencies:
```bash
pip install -r requirements.txt
```

### 4. Configuration
Set the environment variable for your PostgreSQL Database connection string:

**Windows (PowerShell):**
```powershell
$env:DATABASE_URL="postgresql://username:password@localhost/quizdb"
```

**Linux/Mac:**
```bash
export DATABASE_URL="postgresql://username:password@localhost/quizdb"
```

### 5. Initialize the Schema
Run the database setup script to create the necessary tables:
```bash
python setup_db.py
```

### 6. Run the Server
Start the FastAPI server using Uvicorn:
```bash
uvicorn app.main:app --reload
```

### 7. Access the Application
- **Web App**: Open http://localhost:8000 in your browser.
- **API Documentation**: http://localhost:8000/docs (Swagger UI)

---

## Deployment (Render)

This project is configured for easy deployment on Render via the included `render.yaml` blueprint.

1. Push your repository to GitHub.
2. Go to the Render Dashboard and create a new **PostgreSQL** database.
3. Click "New" > "Blueprint" and connect your GitHub repository.
4. Render will automatically read the `render.yaml` file, detect the PostgreSQL database, inject the `DATABASE_URL` environment variable, and build your FastAPI web service.

---

## Project Structure
```text
online-quiz-system/
│
├── app/
│   ├── main.py              # App entry point & Router setup
│   ├── database.py          # PostgreSQL connection pool
│   ├── auth.py              # JWT & Auth Endpoints
│   ├── schemas.py           # Pydantic validation models
│   ├── quiz_routes.py       # Quiz & Attempt management
│   ├── analytics_routes.py  # Performance stats
│   └── utils.py             # Hashing helpers
│
├── database/
│   └── schema.sql           # PostgreSQL DDL
│
├── frontend/                # HTML Templates
│   ├── index.html
│   ├── dashboard.html
│   ├── quiz.html
│   └── results.html
│
├── static/
│   ├── css/style.css        # Premium Styling
│   └── js/api.js            # Fetch API Handler
│
├── render.yaml              # Render deployment configuration
├── setup_db.py              # Schema initialization script
└── requirements.txt         # Dependencies
```
