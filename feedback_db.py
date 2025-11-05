# IMPORTER
import sqlite3
from datetime import datetime
import csv
import io
import json

# DATABAS - INITIERING & TABELLER
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saved_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    conn.commit()
    return conn

# FEEDBACK - SPARA & HÄMTA
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

# FEEDBACK - EXPORTER
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

# MEDDELANDEN - SPARA & LADDA
def save_message(conn, *, conversation_id, role, content, timestamp) -> None:
    created_at = datetime.utcnow().isoformat()
    conn.execute("""
        INSERT INTO messages (conversation_id, role, content, timestamp, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (conversation_id, role, content, timestamp, created_at))
    conn.commit()

def load_messages(conn, conversation_id: str) -> list:
    rows = conn.execute("""
        SELECT role, content, timestamp
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
    """, (conversation_id,)).fetchall()
    return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in rows]

def delete_messages(conn, conversation_id: str) -> None:
    conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    conn.commit()

# KONVERSATIONER - HANTERING
def create_or_update_conversation(conn, conversation_id: str) -> None:
    now = datetime.utcnow().isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO conversations (id, created_at, updated_at)
        VALUES (?, COALESCE((SELECT created_at FROM conversations WHERE id = ?), ?), ?)
    """, (conversation_id, conversation_id, now, now))
    conn.commit()

def get_all_conversations(conn) -> list:
    rows = conn.execute("""
        SELECT id, created_at, updated_at
        FROM conversations
        ORDER BY updated_at DESC
    """).fetchall()
    return [{"id": r[0], "created_at": r[1], "updated_at": r[2]} for r in rows]

def delete_conversation(conn, conversation_id: str) -> None:
    conn.execute("DELETE FROM feedback WHERE conversation_id = ?", (conversation_id,))
    conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()

# SPARADE PROMPTS - HANTERING
def save_prompt(conn, name: str, content: str, description: str = "") -> None:
    now = datetime.utcnow().isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO saved_prompts (name, content, description, created_at, updated_at)
        VALUES (?, ?, ?, COALESCE((SELECT created_at FROM saved_prompts WHERE name = ?), ?), ?)
    """, (name, content, description, name, now, now))
    conn.commit()

def get_all_prompts(conn) -> list:
    rows = conn.execute("""
        SELECT name, content, description
        FROM saved_prompts
        ORDER BY updated_at DESC
    """).fetchall()
    return [{"name": r[0], "content": r[1], "description": r[2] or ""} for r in rows]

def delete_prompt(conn, name: str) -> None:
    conn.execute("DELETE FROM saved_prompts WHERE name = ?", (name,))
    conn.commit()

