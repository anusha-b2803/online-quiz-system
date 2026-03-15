from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.database import get_db_cursor, execute_query
from app.schemas import QuizCreate, QuizOut, QuizWithQuestionsOut, QuestionOut, QuizSubmit, AttemptOut
from app.auth import get_current_user, get_current_teacher, get_current_student

router = APIRouter(prefix="/quizzes", tags=["quizzes"])

@router.get("/", response_model=List[dict])  # Changed from List[QuizOut] to dict as we're extending schema
def get_all_quizzes(current_user: dict = Depends(get_current_user)):
    """Get list of available quizzes (Filtered for students)."""
    if current_user["role"] == "STUDENT":
        query = """
            SELECT q.QUIZ_ID, q.TITLE, q.DESCRIPTION, q.TIME_LIMIT, q.CREATED_BY, u.NAME, q.MAX_ATTEMPTS,
                   (SELECT COUNT(*) FROM ATTEMPTS a WHERE a.QUIZ_ID = q.QUIZ_ID AND a.STUDENT_ID = %s) as attempted_count
            FROM QUIZZES q
            JOIN USERS u ON q.CREATED_BY = u.USER_ID
            WHERE q.ASSIGN_TO_ALL = 1 
               OR q.QUIZ_ID IN (SELECT QUIZ_ID FROM QUIZ_ASSIGNMENTS WHERE STUDENT_ID = %s)
        """
        params = (current_user["user_id"], current_user["user_id"])
        rows = execute_query(query, params, fetch_all=True)
        return [
            {
                "quiz_id": r[0],
                "title": r[1],
                "description": r[2],
                "time_limit": r[3],
                "created_by": r[4],
                "created_by_name": r[5],
                "max_attempts": r[6],
                "attempted_count": r[7]
            } for r in rows
        ]
    else:  # TEACHER
        query = """
            SELECT q.QUIZ_ID, q.TITLE, q.DESCRIPTION, q.TIME_LIMIT, q.CREATED_BY, u.NAME, q.MAX_ATTEMPTS
            FROM QUIZZES q
            JOIN USERS u ON q.CREATED_BY = u.USER_ID
            WHERE q.CREATED_BY = %s
        """
        params = (current_user["user_id"],)
        rows = execute_query(query, params, fetch_all=True)
        return [
            {
                "quiz_id": r[0],
                "title": r[1],
                "description": r[2],
                "time_limit": r[3],
                "created_by": r[4],
                "created_by_name": r[5],
                "max_attempts": r[6]
            } for r in rows
        ]

@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_quiz(quiz_data: QuizCreate, current_teacher: dict = Depends(get_current_teacher)):
    """Create a new quiz (Teacher only)."""
    with get_db_cursor() as cursor:
        try:
            # 1. Insert Quiz
            quiz_sql = """
                INSERT INTO QUIZZES (TITLE, DESCRIPTION, TIME_LIMIT, CREATED_BY, ASSIGN_TO_ALL, MAX_ATTEMPTS)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING QUIZ_ID
            """
            cursor.execute(quiz_sql, (
                quiz_data.title,
                quiz_data.description,
                quiz_data.time_limit,
                current_teacher["user_id"],
                1 if quiz_data.assign_to_all else 0,
                quiz_data.max_attempts
            ))
            quiz_id = cursor.fetchone()[0]

            # 2. Insert Questions
            question_sql = """
                INSERT INTO QUESTIONS (QUIZ_ID, QUESTION_TEXT, OPTION1, OPTION2, OPTION3, OPTION4, CORRECT_OPTION, DIFFICULTY)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            for q in quiz_data.questions:
                cursor.execute(question_sql, (
                    quiz_id,
                    q.question_text,
                    q.option1,
                    q.option2,
                    q.option3,
                    q.option4,
                    q.correct_option,
                    q.difficulty.upper()
                ))

            # 3. Insert Specific Assignments (if not all)
            if not quiz_data.assign_to_all and quiz_data.assigned_students:
                assign_sql = "INSERT INTO QUIZ_ASSIGNMENTS (QUIZ_ID, STUDENT_ID) VALUES (%s, %s)"
                for student_id in quiz_data.assigned_students:
                    cursor.execute(assign_sql, (quiz_id, student_id))
                
            return {"message": "Quiz created successfully", "quiz_id": quiz_id}
            
        except Exception as e:
            # Context manager handles rollback
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database Error: {str(e)}"
            )

@router.get("/{quiz_id}", response_model=QuizWithQuestionsOut)
def get_quiz(quiz_id: int, current_user: dict = Depends(get_current_user)):
    """Get specific quiz details with questions."""
    # 1. Get Quiz info
    quiz_query = "SELECT QUIZ_ID, TITLE, DESCRIPTION, TIME_LIMIT, CREATED_BY, MAX_ATTEMPTS FROM QUIZZES WHERE QUIZ_ID = %s"
    quiz_row = execute_query(quiz_query, (quiz_id,), fetch_one=True)
    if not quiz_row:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Access / Limit checks for students
    if current_user["role"] == "STUDENT":
        max_attempts = quiz_row[5]
        if max_attempts > 0:
            limit_query = "SELECT COUNT(*) FROM ATTEMPTS WHERE QUIZ_ID = %s AND STUDENT_ID = %s"
            limit_row = execute_query(limit_query, (quiz_id, current_user["user_id"]), fetch_one=True)
            if limit_row and limit_row[0] >= max_attempts:
                raise HTTPException(status_code=403, detail=f"Maximum attempts ({max_attempts}) reached for this quiz. You cannot start it again.")

    # 2. Get Questions
    q_query = """
        SELECT QUESTION_ID, QUIZ_ID, QUESTION_TEXT, OPTION1, OPTION2, OPTION3, OPTION4, CORRECT_OPTION, DIFFICULTY 
        FROM QUESTIONS WHERE QUIZ_ID = %s
    """
    q_rows = execute_query(q_query, (quiz_id,), fetch_all=True)
    
    questions = []
    for r in q_rows:
        questions.append({
            "question_id": r[0],
            "quiz_id": r[1],
            "question_text": r[2],
            "option1": r[3],
            "option2": r[4],
            "option3": r[5],
            "option4": r[6],
            "correct_option": r[7],
            "difficulty": r[8]
        })

    return {
        "quiz_id": quiz_row[0],
        "title": quiz_row[1],
        "description": quiz_row[2],
        "time_limit": quiz_row[3],
        "created_by": quiz_row[4],
        "questions": questions
    }

@router.post("/{quiz_id}/submit", status_code=status.HTTP_201_CREATED)
def submit_quiz(quiz_id: int, submission: QuizSubmit, current_student: dict = Depends(get_current_student)):
    """Submit quiz answers and calculate score (Student only)."""
    with get_db_cursor() as cursor:
        try:
            # 1. Verify Quiz exists and get limit
            cursor.execute("SELECT QUIZ_ID, MAX_ATTEMPTS FROM QUIZZES WHERE QUIZ_ID = %s", (quiz_id,))
            quiz_row = cursor.fetchone()
            if not quiz_row:
                raise HTTPException(status_code=404, detail="Quiz not found")
            
            max_attempts = quiz_row[1]

            # 1b. Check current attempt count for student
            if max_attempts > 0:
                cursor.execute("SELECT COUNT(*) FROM ATTEMPTS WHERE QUIZ_ID = %s AND STUDENT_ID = %s", (quiz_id, current_student["user_id"]))
                attempts_count = cursor.fetchone()[0]
                if attempts_count >= max_attempts:
                    raise HTTPException(status_code=403, detail=f"Maximum attempts ({max_attempts}) reached for this quiz.")

            # 2. Fetch correct answers for comparison
            cursor.execute("SELECT QUESTION_ID, CORRECT_OPTION FROM QUESTIONS WHERE QUIZ_ID = %s", (quiz_id,))
            answer_key = {row[0]: row[1] for row in cursor.fetchall()}

            # 3. Calculate Score
            score = 0
            correct_count = 0
            total_questions = len(answer_key)

            # Insert Attempt first to get ATTEMPT_ID
            attempt_sql = """
                INSERT INTO ATTEMPTS (STUDENT_ID, QUIZ_ID, SCORE, TIME_TAKEN)
                VALUES (%s, %s, %s, %s)
                RETURNING ATTEMPT_ID
            """
            # Score first
            answers_to_insert = []
            for ans in submission.answers:
                q_id = ans.question_id
                selected = ans.selected_option
                is_correct = 0
                
                if q_id in answer_key:
                    if selected == answer_key[q_id]:
                        score += 1 # 1 point per question
                        correct_count += 1
                        is_correct = 1
                    
                    answers_to_insert.append({
                        "question_id": q_id,
                        "selected_option": selected,
                        "is_correct": is_correct
                    })

            # Insert Attempt
            cursor.execute(attempt_sql, (
                current_student["user_id"],
                quiz_id,
                score,
                submission.time_taken
            ))
            attempt_id = cursor.fetchone()[0]

            # Insert Answers
            ans_sql = """
                INSERT INTO ANSWERS (ATTEMPT_ID, QUESTION_ID, SELECTED_OPTION, IS_CORRECT)
                VALUES (%s, %s, %s, %s)
            """
            for a in answers_to_insert:
                cursor.execute(ans_sql, (
                    attempt_id,
                    a["question_id"],
                    a["selected_option"],
                    a["is_correct"]
                ))

            return {
                "message": "Quiz submitted successfully",
                "attempt_id": attempt_id,
                "score": score,
                "total_questions": total_questions,
                "correct_answers": correct_count
            }

        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

@router.get("/attempts/{attempt_id}")
def get_attempt_details(attempt_id: int, current_user: dict = Depends(get_current_user)):
    """Get details of a specific attempt including answers."""
    # 1. Get Attempt
    attempt_query = """
        SELECT ATTEMPT_ID, STUDENT_ID, QUIZ_ID, SCORE, ATTEMPT_DATE, TIME_TAKEN 
        FROM ATTEMPTS WHERE ATTEMPT_ID = %s
    """
    attempt_row = execute_query(attempt_query, (attempt_id,), fetch_one=True)
    if not attempt_row:
        raise HTTPException(status_code=404, detail="Attempt not found")

    # Access check: Only student who took it OR teacher can see it
    if current_user["role"] == "STUDENT" and attempt_row[1] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # 2. Get Answers
    ans_query = """
        SELECT ans.QUESTION_ID, ans.SELECTED_OPTION, ans.IS_CORRECT, q.QUESTION_TEXT
        FROM ANSWERS ans
        JOIN QUESTIONS q ON ans.QUESTION_ID = q.QUESTION_ID
        WHERE ans.ATTEMPT_ID = %s
    """
    ans_rows = execute_query(ans_query, (attempt_id,), fetch_all=True)

    return {
        "attempt_id": attempt_row[0],
        "student_id": attempt_row[1],
        "quiz_id": attempt_row[2],
        "score": attempt_row[3],
        "attempt_date": attempt_row[4],
        "time_taken": attempt_row[5],
        "answers": [
            {
                "question_id": r[0],
                "selected_option": r[1],
                "is_correct": r[2],
                "question_text": r[3]
            } for r in ans_rows
        ]
    }
