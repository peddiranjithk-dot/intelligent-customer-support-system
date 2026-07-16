"""
database.py
Handles SQLite storage for chat logs and escalated support tickets.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "support_system.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            matched_intent TEXT,
            confidence REAL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            priority TEXT NOT NULL DEFAULT 'normal',
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def log_chat(session_id, user_message, bot_response, matched_intent, confidence):
    conn = get_connection()
    conn.execute(
        """INSERT INTO chat_logs
           (session_id, user_message, bot_response, matched_intent, confidence, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (session_id, user_message, bot_response, matched_intent, confidence,
         datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def create_ticket(session_id, subject, message, priority="normal"):
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO tickets (session_id, subject, message, status, priority, created_at)
           VALUES (?, ?, ?, 'open', ?, ?)""",
        (session_id, subject, message, priority, datetime.utcnow().isoformat()),
    )
    conn.commit()
    ticket_id = cur.lastrowid
    conn.close()
    return ticket_id


def get_all_tickets():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM tickets ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_ticket_status(ticket_id, status):
    conn = get_connection()
    conn.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
    conn.commit()
    conn.close()


def get_chat_history(session_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM chat_logs WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
