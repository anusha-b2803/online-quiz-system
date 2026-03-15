import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://quiz_user:quiz_password@localhost/quizdb")

print(f"Connecting to PostgreSQL...")

try:
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    print("Connected. Reading schema.sql...")

    with open("database/schema.sql", "r") as f:
        content = f.read()

    # For PostgreSQL, we can often execute the entire script at once if separated by statements.
    # psycopg2 cursor.execute() can handle multiple statements natively.
    print("Executing schema setup...")
    cursor.execute(content)
    connection.commit()
    
    print("✅ Database Setup Complete!")
    cursor.close()
    connection.close()

except Exception as e:
    print(f"❌ Setup Failed: {e}")
