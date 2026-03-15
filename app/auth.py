from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os

from app.schemas import TokenData, UserCreate, UserLogin, Token
from app.database import execute_query, get_db_cursor
from app.utils import get_password_hash, verify_password

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-jwt-change-it-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    """Register a new user."""
    # Check if email exists
    query = "SELECT USER_ID FROM USERS WHERE EMAIL = %s"
    if execute_query(query, (user.email,), fetch_one=True):
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_pass = get_password_hash(user.password)
    
    with get_db_cursor() as cursor:
        try:
            sql = """
                INSERT INTO USERS (NAME, EMAIL, PASSWORD, ROLE)
                VALUES (%s, %s, %s, %s)
                RETURNING USER_ID
            """
            cursor.execute(sql, (
                user.name,
                user.email,
                hashed_pass,
                user.role.upper()
            ))
            # No need to use bind-vars for RETURNING in psycopg2, it returns like a SELECT
            # but we aren't reading the ID here anyway, we just return success.
            return {"message": "User registered successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=Token)
def login_user(user_data: UserLogin):
    """Login to get access token."""
    query = "SELECT USER_ID, EMAIL, PASSWORD, ROLE FROM USERS WHERE EMAIL = %s"
    row = execute_query(query, (user_data.email,), fetch_one=True)
    
    if not row:
        raise HTTPException(status_code=400, detail="Invalid credentials")
        
    user_id, email, hashed_password, role = row
    
    if not verify_password(user_data.password, hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
        
    access_token = create_access_token(
        data={"sub": email, "user_id": user_id, "role": role}
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": role,
        "user_id": user_id
    }

# --- Dependencies move below ---

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        user_id: int = payload.get("user_id")
        if email is None or user_id is None:
            raise credentials_exception
        token_data = TokenData(email=email, role=role, user_id=user_id)
    except JWTError:
        raise credentials_exception
        
    # Verify user exists in DB
    query = "SELECT USER_ID, NAME, EMAIL, ROLE FROM USERS WHERE USER_ID = %s"
    row = execute_query(query, (token_data.user_id,), fetch_one=True)
    if row is None:
        raise credentials_exception
        
    return {
        "user_id": row[0],
        "name": row[1],
        "email": row[2],
        "role": row[3]
    }

async def get_current_teacher(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Teacher role required."
        )
    return current_user

async def get_current_student(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Student role required."
        )
    return current_user

@router.get("/students")
def get_students(current_user: dict = Depends(get_current_teacher)):
    """Get list of all students (Teacher only)."""
    from app.database import execute_query
    query = "SELECT USER_ID, NAME, EMAIL FROM USERS WHERE ROLE = 'STUDENT'"
    rows = execute_query(query, fetch_all=True)
    return [{"user_id": r[0], "name": r[1], "email": r[2]} for r in rows]
