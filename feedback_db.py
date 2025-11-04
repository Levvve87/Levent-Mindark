import sqlite3
from datetime import datetime
import csv
import io
import json


def init_db(db_path: str = "feedback.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("""
     CREATE TABLE IF NOT EXISTS feedback (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      conversation_id TEXT,
      message_index INTEGER NOT NULL,
      role TEXT NOT NULL,
      rating TEXT NOT NULL CHECK (rating IN ('up','down')),
      reason TEXT,
      message_content TEXT,
      created_at TEXT NOT NULL
    );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_conversation ON feedback(conversation_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback(rating);")
    conn.commit()
    return conn


def save_feedback(conn, *, conversation_id, message_index, role, rating, reason, message_content) -> None:
    created_at = datetime.utcnow().isoformat()
    conn.execute("""
      INSERT INTO feedback (conversation_id, message_index, role, rating, reason, message_content, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
      conversation_id or None,
      message_index,
      role,
      rating,
      reason or None,
      message_content or None,
      created_at
    ))
    conn.commit()

def get_feedback_summary(conn) -> dict:
    rows = conn.execute("""
      SELECT rating, COUNT(*) as cnt
      FROM feedback
      GROUP BY rating
    """).fetchall()
    summary = {"up": 0, "down": 0}
    for rating, cnt in rows:
        summary[rating] = cnt
    return summary

def get_recent_feedback(conn, limit: int = 50) -> list[tuple]:
    rows = conn.execute(
        """
      SELECT id, conversation_id, message_index, role, rating, reason, message_content, created_at
      FROM feedback
      ORDER BY created_at DESC
      LIMIT ?
    """,
        (limit,),
    ).fetchall()
    return rows

def export_feedback_csv(conn) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id","conversation_id","message_index","role","rating","reason","message_content","created_at"])
    for row in conn.execute("""
        SELECT id, conversation_id, message_index, role, rating, reason, message_content, created_at
        FROM feedback
        ORDER BY id ASC
    """):
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


def export_feedback_json(conn) -> str:
    rows = conn.execute("""
        SELECT id, conversation_id, message_index, role, rating, reason, message_content, created_at
        FROM feedback
        ORDER BY id ASC
    """).fetchall()
    cols = ["id","conversation_id","message_index","role","rating","reason","message_content","created_at"]
    as_dicts = [dict(zip(cols, r)) for r in rows]
    return json.dumps(as_dicts, ensure_ascii=False, indent=2)

