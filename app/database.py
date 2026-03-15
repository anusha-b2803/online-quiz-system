import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager

# PostgreSQL Database Connection Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://quiz_user:quiz_password@localhost/quizdb")

db_pool = None

def get_pool():
    global db_pool
    if db_pool is None:
        try:
            db_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20, dsn=DATABASE_URL
            )
            print("PostgreSQL Database Connection Pool created.")
        except Exception as e:
            print(f"Error creating connection pool: {e}")
            raise e
    return db_pool

@contextmanager
def get_db_cursor():
    """
    Context manager to safely get a database connection and cursor.
    Ensures connection is returned to the pool and errors are handled.
    """
    p = get_pool()
    connection = p.getconn()
    cursor = connection.cursor()
    try:
        yield cursor
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        p.putconn(connection)

def execute_query(query: str, params: tuple = None, fetch_one = False, fetch_all = False):
    """
    Helper function to execute a query and fetch results safely from pool.
    """
    with get_db_cursor() as cursor:
        cursor.execute(query, params or ())
        if fetch_one:
            return cursor.fetchone()
        if fetch_all:
            return cursor.fetchall()
        return None

def execute_insert(query: str, params: tuple = None):
    """
    Helper function to execute an INSERT/UPDATE/DELETE with return value.
    Usually for RETURNING clause.
    """
    with get_db_cursor() as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchone()
