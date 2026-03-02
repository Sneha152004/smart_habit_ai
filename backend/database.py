import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'habit_tracker.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # User Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # Daily Logs Table - Ensuring all columns exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            sleep_hours REAL,
            study_hours REAL,
            workout_minutes REAL,
            journal_minutes REAL,
            reading_minutes REAL,
            mood INTEGER,
            p_slip_prob REAL,
            motivation_score REAL,
            difficulty_adjustment TEXT,
            streak_protection INTEGER,
            bad_day INTEGER,
            burnout_risk REAL,
            weakest_habit TEXT,
            recommendation TEXT,
            timer_seconds INTEGER,
            norms TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
