from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any, Dict
from app.database import execute_query
from app.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary/{quiz_id}")
def get_quiz_summary(quiz_id: int, current_user: dict = Depends(get_current_user)):
    """Get basic stats for a quiz: Average Score, High Score, Total Attempts."""
    query = """
        SELECT 
            AVG(SCORE) as avg_score,
            MAX(SCORE) as max_score,
            COUNT(ATTEMPT_ID) as total_attempts
        FROM ATTEMPTS 
        WHERE QUIZ_ID = %s
    """
    row = execute_query(query, (quiz_id,), fetch_one=True)
    
    if not row or row[2] == 0:
        return {
            "avg_score": 0,
            "max_score": 0,
            "total_attempts": 0
        }
        
    return {
        "avg_score": float(row[0]) if row[0] is not None else 0,
        "max_score": int(row[1]) if row[1] is not None else 0,
        "total_attempts": int(row[2])
    }

@router.get("/leaderboard/{quiz_id}")
def get_leaderboard(quiz_id: int, current_user: dict = Depends(get_current_user)):
    """Get Top 10 students for a quiz ranked by score and time taken."""
    query = """
        SELECT u.NAME, a.SCORE, a.TIME_TAKEN, a.ATTEMPT_DATE, a.STUDENT_ID
        FROM ATTEMPTS a
        JOIN USERS u ON a.STUDENT_ID = u.USER_ID
        WHERE a.QUIZ_ID = %s
        ORDER BY a.SCORE DESC, a.TIME_TAKEN ASC
        LIMIT 10
    """
    rows = execute_query(query, (quiz_id,), fetch_all=True)
    return [
        {
            "name": r[0],
            "score": r[1],
            "time_taken": r[2],
            "date": r[3],
            "student_id": r[4]
        } for r in rows
    ]

@router.get("/student_profile/{student_id}")
def get_student_profile(student_id: int, current_user: dict = Depends(get_current_user)):
    """Get statistics and history of a student for the teacher."""
    if current_user.get("role") != "TEACHER":
        raise HTTPException(status_code=403, detail="Access denied. Teachers only.")
    
    stats_query = """
        SELECT COUNT(ATTEMPT_ID), AVG(SCORE), COALESCE(SUM(SCORE), 0)
        FROM ATTEMPTS WHERE STUDENT_ID = %s
    """
    history_query = """
        SELECT q.TITLE, a.SCORE, a.ATTEMPT_DATE
        FROM ATTEMPTS a 
        JOIN QUIZZES q ON a.QUIZ_ID = q.QUIZ_ID
        WHERE a.STUDENT_ID = %s 
        ORDER BY a.ATTEMPT_DATE DESC
    """
    stats_row = execute_query(stats_query, (student_id,), fetch_one=True)
    history_rows = execute_query(history_query, (student_id,), fetch_all=True)
    
    return {
        "stats": {
            "quizzes_taken": stats_row[0] if stats_row else 0,
            "avg_score": float(stats_row[1]) if stats_row and stats_row[1] else 0,
            "total_score": int(stats_row[2]) if stats_row else 0
        },
        "history": [
            {"quiz_title": r[0], "score": r[1], "date": r[2]} for r in history_rows
        ]
    }

@router.get("/difficult_questions/{quiz_id}")
def get_difficult_questions(quiz_id: int, current_user: dict = Depends(get_current_user)):
    """Get questions with the lowest correct answer rate."""
    query = """
        SELECT q.QUESTION_ID, q.QUESTION_TEXT,
               SUM(CASE WHEN ans.IS_CORRECT = 1 THEN 1 ELSE 0 END) as correct_count,
               COUNT(ans.ANSWER_ID) as total_answers
        FROM QUESTIONS q
        JOIN ANSWERS ans ON q.QUESTION_ID = ans.QUESTION_ID
        WHERE q.QUIZ_ID = %s
        GROUP BY q.QUESTION_ID, q.QUESTION_TEXT
        ORDER BY (SUM(CASE WHEN ans.IS_CORRECT = 1 THEN 1.0 ELSE 0.0 END) / NULLIF(COUNT(ans.ANSWER_ID), 0)) ASC NULLS LAST
        LIMIT 5
    """
    rows = execute_query(query, (quiz_id,), fetch_all=True)
    return [
        {
            "question_id": r[0],
            "question_text": r[1],
            "correct_count": r[2],
            "total_answers": r[3],
            "correct_rate": float(r[2])/r[3] if r[3] > 0 else 0
        } for r in rows
    ]

@router.get("/student_stats")
def get_student_stats(current_user: dict = Depends(get_current_user)):
    """Get overall stats for the logged-in student."""
    query = """
        SELECT 
            COUNT(ATTEMPT_ID) as quizzes_taken,
            AVG(SCORE) as avg_score,
            COALESCE(SUM(SCORE), 0) as total_score
        FROM ATTEMPTS 
        WHERE STUDENT_ID = %s
    """
    row = execute_query(query, (current_user["user_id"],), fetch_one=True)
    return {
        "quizzes_taken": row[0] if row else 0,
        "avg_score": float(row[1]) if row and row[1] else 0,
        "total_score": int(row[2]) if row else 0
    }

@router.get("/my_attempts")
def get_my_attempts(current_user: dict = Depends(get_current_user)):
    """Get list of past attempts for the logged-in student."""
    query = """
        SELECT a.ATTEMPT_ID, a.QUIZ_ID, q.TITLE, a.SCORE, a.ATTEMPT_DATE, a.TIME_TAKEN
        FROM ATTEMPTS a
        JOIN QUIZZES q ON a.QUIZ_ID = q.QUIZ_ID
        WHERE a.STUDENT_ID = %s
        ORDER BY a.ATTEMPT_DATE DESC
    """
    rows = execute_query(query, (current_user["user_id"],), fetch_all=True)
    return [
        {
            "attempt_id": r[0],
            "quiz_id": r[1],
            "quiz_title": r[2],
            "score": r[3],
            "date": r[4],
            "time_taken": r[5]
        } for r in rows
    ]
