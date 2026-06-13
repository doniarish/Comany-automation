import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_SCHEMA = """
TABLE users (
  id INT PRIMARY KEY,
  username VARCHAR(50),
  password VARCHAR(255),
  role ENUM('manager', 'employee'),
  manager_id INT
);

TABLE tasks (
  id INT PRIMARY KEY,
  title VARCHAR(255),
  description TEXT,
  employee_id INT,
  status ENUM('pending', 'in_progress', 'completed'),
  created_at TIMESTAMP
);
"""

def execute_query(query: str, params: tuple = ()):
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", ""),
            database=os.getenv("DB_NAME", "company_automation")
        )
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.lastrowid
            return result
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        return f"Error executing query: {str(e)}"
