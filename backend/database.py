import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.getenv("DB_PATH", "chatanalytic.db")

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # chats
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                chat_mode TEXT DEFAULT 'group',
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_file_deleted BOOLEAN DEFAULT 0
            )
        ''')
        
        # report_cache: stores LLM output so repeated calls are instant + identical
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_cache (
                chat_id INTEGER PRIMARY KEY,
                ai_roast_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        
        # participants
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                display_name TEXT,
                normalized_name TEXT,
                FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
            )
        ''')
        
        # messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                sender_id INTEGER,
                timestamp TIMESTAMP,
                text TEXT,
                message_type TEXT,
                FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE,
                FOREIGN KEY (sender_id) REFERENCES participants (id) ON DELETE CASCADE
            )
        ''')
        
        # pattern_results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                pattern_key TEXT,
                triggered BOOLEAN,
                evidence_json TEXT,
                score REAL,
                FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
            )
        ''')
        
        # relationship_scores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relationship_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                participant_a_id INTEGER,
                participant_b_id INTEGER,
                avg_reply_time_a_to_b REAL,
                avg_reply_time_b_to_a REAL,
                initiation_ratio REAL,
                closeness_score REAL,
                FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = 1")
    try:
        yield conn
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
