from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import os

from app.auth import router as auth_router
from app.quiz_routes import router as quiz_router
from app.analytics_routes import router as analytics_router
from app.database import get_pool

app = FastAPI(title="Online Quiz System API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API ROUTES ---
# API Routes prefixed with /api
app.include_router(auth_router, prefix="/api")
app.include_router(quiz_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")

# --- PAGE ROUTES (Frontend) ---
@app.get("/")
def home():
    return FileResponse("frontend/index.html")

@app.get("/login")
def login_page():
    return FileResponse("frontend/login.html")

@app.get("/register")
def register_page():
    return FileResponse("frontend/register.html")

@app.get("/dashboard")
def dashboard_page():
    return FileResponse("frontend/dashboard.html")

@app.get("/create_quiz")
def create_quiz_page():
    return FileResponse("frontend/create_quiz.html")

@app.get("/quiz")
def quiz_page():
    return FileResponse("frontend/quiz.html")

@app.get("/results")
def results_page():
    return FileResponse("frontend/results.html")

@app.get("/analytics")
def analytics_page():
    return FileResponse("frontend/analytics.html")


# Ensure directories exist for static files and frontend
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("frontend", exist_ok=True)

# Mount Static Files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount Frontend Files (HTML) as fallback for old .html links
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

@app.on_event("startup")
def startup():
    print("Initializing Database Pool...")
    get_pool()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
