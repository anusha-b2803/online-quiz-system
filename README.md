# Online Quiz System with Performance Analytics

A production-style REST API based quiz platform built with **FastAPI** and **Oracle Database**.

## 🚀 Features
- **User Authentication**: Secure Registration & Login (JWT + Hashing) for Students & Teachers.
- **Quiz Management**: Teachers can create quizzes with multiple options and difficulty levels.
- **Quiz Attempt**: Students can take quizzes with real-time timers.
- **Performance Analytics**: Average scores, Leaderboards, and Toughest Questions tracking.
- **Modern UI**: Dark-mode glassmorphic interface.

---

## 🛠️ Tech Stack
- **Backend**: FastAPI (Python)
- **Database**: Oracle SQL via `python-oracledb`
- **Frontend**: HTML5, CSS3 (Glassmorphism), Vanilla JavaScript (Fetch API)

---

## 🏃‍♂️ Getting Started

### 1. Prerequisites
- **Python 3.8+**
- **Oracle Database** (Local XE or Cloud)
- Oracle Account with access to execute DDLs.

### 2. Database Setup
Execute the contents of `database/schema.sql` in your Oracle Database tool (SQL*Plus, SQL Developer, or Oracle Cloud Console).
This will create the following tables:
- `USERS`
- `QUIZZES`
- `QUESTIONS`
- `ATTEMPTS`
- `ANSWERS`

### 3. Installation
Clone or navigate to the project directory and install dependencies:
```bash
pip install -r requirements.txt
```

### 4. Configuration
Set environment variables for your Oracle Database credentials:

**Windows (PowerShell):**
```powershell
$env:ORACLE_USER="your_username"
$env:ORACLE_PASSWORD="your_password"
$env:ORACLE_DSN="localhost/XEPDB1"
```

**Linux/Mac:**
```bash
export ORACLE_USER="your_username"
export export ORACLE_PASSWORD="your_password"
export ORACLE_DSN="localhost/XEPDB1"
```

### 5. Run the Server
Start the FastAPI server using Uvicorn:
```bash
uvicorn app.main:app --reload
```

### 6. Access the Application
- **Web App**: Open [http://localhost:8000](http://localhost:8000) in your browser.
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)

---

## 📁 Project Structure
```text
online-quiz-system/
│
├── app/
│   ├── main.py              # App entry point & Router setup
│   ├── database.py          # Oracle connection pool
│   ├── auth.py              # JWT & Auth Endpoints
│   ├── schemas.py           # Pydantic validation models
│   ├── quiz_routes.py       # Quiz & Attempt management
│   ├── analytics_routes.py  # Performance stats
│   └── utils.py             # Hashing helpers
│
├── database/
│   └── schema.sql           # Oracle DDL
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
└── requirements.txt         # Dependencies
```
