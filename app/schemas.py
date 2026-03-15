from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import date

# --- USER SCHEMAS ---
class UserBase(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=4)
    role: str = Field(..., description="TEACHER or STUDENT")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    user_id: int
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None

# --- QUESTION SCHEMAS ---
class QuestionBase(BaseModel):
    question_text: str = Field(..., max_length=500)
    option1: str = Field(..., max_length=200)
    option2: str = Field(..., max_length=200)
    option3: str = Field(..., max_length=200)
    option4: str = Field(..., max_length=200)
    correct_option: int = Field(..., ge=1, le=4)
    difficulty: str = Field("MEDIUM", description="EASY, MEDIUM, HARD")

class QuestionCreate(QuestionBase):
    pass

class QuestionOut(QuestionBase):
    question_id: int
    quiz_id: int

# --- QUIZ SCHEMAS ---
class QuizBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    time_limit: int = Field(..., description="Time limit in minutes")

class QuizCreate(QuizBase):
    assign_to_all: bool = True
    assigned_students: List[int] = [] 
    max_attempts: int = 0 # 0 means Unlimited
    questions: List[QuestionCreate]

class QuizOut(QuizBase):
    quiz_id: int
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    max_attempts: Optional[int] = 0

class QuizWithQuestionsOut(QuizOut):
    questions: List[QuestionOut]

# --- ATTEMPT SCHEMAS ---
class AnswerSubmit(BaseModel):
    question_id: int
    selected_option: int

class QuizSubmit(BaseModel):
    answers: List[AnswerSubmit]
    time_taken: int # in seconds

class AttemptOut(BaseModel):
    attempt_id: int
    student_id: int
    quiz_id: int
    score: int
    attempt_date: date
    time_taken: int
