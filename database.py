import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edupilot.db')

def get_connection():
    """Create a database connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def get_db():
    """Context manager for safe database transactions."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database tables according to specification."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                preferred_language TEXT DEFAULT 'English',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Study sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                date TEXT NOT NULL,
                duration INTEGER NOT NULL,
                notes TEXT,
                completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        ''')

        # Quizzes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        ''')

        # Weak topics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weak_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'Needs Review',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        ''')

        # Notes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                raw_text TEXT,
                summary_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        ''')

        # Chat messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                sender TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        ''')

def seed_demo_data():
    """Seed a realistic demo student profile if it does not already exist."""
    import datetime
    import bcrypt

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = 'demo@edupilot.ai'")
        if cursor.fetchone():
            return  # Already seeded

        # Create demo user (pw: demostudent123)
        salt = bcrypt.gensalt(rounds=12)
        pw_hash = bcrypt.hashpw('demostudent123'.encode('utf-8'), salt).decode('utf-8')
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, preferred_language) VALUES (?, ?, ?, ?)",
            ('Alex Chen', 'demo@edupilot.ai', pw_hash, 'English')
        )
        user_id = cursor.lastrowid
        today = datetime.date.today().isoformat()
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

        # Study sessions
        cursor.execute(
            "INSERT INTO study_sessions (user_id, subject, date, duration, notes, completed) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, "CS 201: Data Structures & Algorithms", today, 60, "Review Binary Search Trees and Big-O runtimes.", 0)
        )
        cursor.execute(
            "INSERT INTO study_sessions (user_id, subject, date, duration, notes, completed) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, "MATH 240: Multivariable Calculus", today, 45, "Solve double integrals and Green's Theorem problem sets.", 1)
        )
        cursor.execute(
            "INSERT INTO study_sessions (user_id, subject, date, duration, notes, completed) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, "ECON 102: Macroeconomic Principles", tomorrow, 50, "Read chapter 8 on Central Bank monetary policy.", 0)
        )

        # Quizzes
        cursor.execute(
            "INSERT INTO quizzes (user_id, topic, score, total_questions) VALUES (?, ?, ?, ?)",
            (user_id, "Data Structures", 4, 5)
        )
        cursor.execute(
            "INSERT INTO quizzes (user_id, topic, score, total_questions) VALUES (?, ?, ?, ?)",
            (user_id, "Calculus", 5, 5)
        )

        # Weak topics
        cursor.execute(
            "INSERT INTO weak_topics (user_id, topic, reason, status) VALUES (?, ?, ?, ?)",
            (user_id, "Dynamic Programming Memoization", "Struggle with identifying the state transition relation for 2D grids", "Needs Review")
        )
        cursor.execute(
            "INSERT INTO weak_topics (user_id, topic, reason, status) VALUES (?, ?, ?, ?)",
            (user_id, "Electromagnetic Induction (Faraday's Law)", "Often get confused about the negative sign in Lenz's law during exam questions", "Needs Review")
        )
        cursor.execute(
            "INSERT INTO weak_topics (user_id, topic, reason, status) VALUES (?, ?, ?, ?)",
            (user_id, "Binary Tree Traversals", "Used to mix up in-order and post-order when reconstructing trees", "Mastered")
        )

        # Notes
        cursor.execute(
            "INSERT INTO notes (user_id, topic, raw_text, summary_text) VALUES (?, ?, ?, ?)",
            (
                user_id,
                "Algorithm Complexity & Big-O",
                "Big-O notation describes the upper bound of execution time as input n grows. O(1) is constant, O(log n) is logarithmic, O(n) is linear, O(n log n) is typical for efficient sorting like MergeSort.",
                "### 🎯 Core Concept Overview: Algorithm Complexity & Big-O\nBig-O notation characterizes the limiting behavior of an algorithm's runtime or memory consumption.\n\n---\n\n### 📌 Key Takeaways\n• O(1): Constant time operations (e.g. array index lookup, hash map retrieval).\n• O(log n): Sub-linear scaling (e.g. binary search on sorted data).\n• O(n): Linear scanning of all elements.\n• O(n log n): Optimal comparison-based sorting limit (MergeSort, HeapSort).\n\n---\n\n### ⚡ Rapid Exam Review\nAlways evaluate the worst-case scenario and watch out for nested loops and recursive stack depth."
            )
        )

        # Chat messages
        cursor.execute(
            "INSERT INTO chat_messages (user_id, message, sender) VALUES (?, ?, ?)",
            (user_id, "Welcome to EduPilot AI, Alex! I am your personal study companion. Ask me anything about your coursework or exam strategies.", "ai")
        )
        cursor.execute(
            "INSERT INTO chat_messages (user_id, message, sender) VALUES (?, ?, ?)",
            (user_id, "Can you explain recursion with a simple example?", "user")
        )
        cursor.execute(
            "INSERT INTO chat_messages (user_id, message, sender) VALUES (?, ?, ?)",
            (user_id, "### 🔄 Understanding Recursion (Step-by-Step)\n\nThink of recursion like Russian Matryoshka dolls! To reach the tiny solid doll inside (the **base case**), you keep opening each outer doll (the **recursive step**).\n\n```python\ndef factorial(n):\n    if n <= 1:           # Base case\n        return 1\n    return n * factorial(n - 1)  # Recursive step\n```\n\nWhat topic would you like to explore next?", "ai")
        )

if __name__ == '__main__':
    init_db()
    seed_demo_data()
    print("Database initialized & seeded successfully at:", DB_PATH)

