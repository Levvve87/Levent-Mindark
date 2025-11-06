# IMPORTER
import sqlite3
from datetime import datetime
import csv
import io
import json

# DATABAS - INITIERING & TABELLER
def init_db(db_path: str = "feedback.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    
    # Kontrollera om gamla feedback-tabellen finns
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback';")
    old_table_exists = cursor.fetchone() is not None
    
    if old_table_exists:
        # Kontrollera om tabellen har gamla rating-kolumnen
        cursor = conn.execute("PRAGMA table_info(feedback);")
        columns = [row[1] for row in cursor.fetchall()]
        if 'rating' in columns and 'rating_type' not in columns:
            # Migrera från gammalt schema till nytt
            conn.execute("""
                CREATE TABLE feedback_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    message_index INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    rating_type TEXT NOT NULL CHECK (rating_type IN ('thumbs','stars')),
                    rating_value INTEGER NOT NULL,
                    reason TEXT,
                    message_content TEXT,
                    created_at TEXT NOT NULL
                );
            """)
            conn.execute("""
                INSERT INTO feedback_new (id, conversation_id, message_index, role, rating_type, rating_value, reason, message_content, created_at)
                SELECT id, conversation_id, message_index, role,
                       'thumbs' as rating_type,
                       CASE WHEN rating = 'up' THEN 1 ELSE -1 END as rating_value,
                       reason, message_content, created_at
                FROM feedback;
            """)
            conn.execute("DROP TABLE feedback;")
            conn.execute("ALTER TABLE feedback_new RENAME TO feedback;")
            conn.commit()
    
    # Skapa tabell med nytt schema om den inte finns
    conn.execute("""
     CREATE TABLE IF NOT EXISTS feedback (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      conversation_id TEXT,
      message_index INTEGER NOT NULL,
      role TEXT NOT NULL,
      rating_type TEXT NOT NULL CHECK (rating_type IN ('thumbs','stars')),
      rating_value INTEGER NOT NULL,
      reason TEXT,
      message_content TEXT,
      created_at TEXT NOT NULL
    );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_conversation ON feedback(conversation_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_rating_type ON feedback(rating_type);")
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
def save_feedback(conn, *, conversation_id, message_index, role, rating_type, rating_value, reason, message_content) -> None:
    created_at = datetime.utcnow().isoformat()
    conn.execute("""
      INSERT INTO feedback (conversation_id, message_index, role, rating_type, rating_value, reason, message_content, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
      conversation_id or None,
      message_index,
      role,
      rating_type,
      rating_value,
      reason or None,
      message_content or None,
      created_at
    ))
    conn.commit()

def get_feedback_summary(conn) -> dict:
    rows = conn.execute("""
      SELECT rating_type, rating_value, COUNT(*) as cnt
      FROM feedback
      GROUP BY rating_type, rating_value
    """).fetchall()
    summary = {"up": 0, "down": 0, "stars": {}}
    for rating_type, rating_value, cnt in rows:
        if rating_type == "thumbs":
            if rating_value == 1:
                summary["up"] += cnt
            elif rating_value == -1:
                summary["down"] += cnt
        elif rating_type == "stars":
            summary["stars"][rating_value] = summary["stars"].get(rating_value, 0) + cnt
    return summary

def get_recent_feedback(conn, limit: int = 50) -> list[tuple]:
    rows = conn.execute(
        """
      SELECT id, conversation_id, message_index, role, rating_type, rating_value, reason, message_content, created_at
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
    writer.writerow(["id","conversation_id","message_index","role","rating_type","rating_value","reason","message_content","created_at"])
    for row in conn.execute("""
        SELECT id, conversation_id, message_index, role, rating_type, rating_value, reason, message_content, created_at
        FROM feedback
        ORDER BY id ASC
    """):
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


def export_feedback_json(conn) -> str:
    rows = conn.execute("""
        SELECT id, conversation_id, message_index, role, rating_type, rating_value, reason, message_content, created_at
        FROM feedback
        ORDER BY id ASC
    """).fetchall()
    cols = ["id","conversation_id","message_index","role","rating_type","rating_value","reason","message_content","created_at"]
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

# DATABAS - RENSNING
def delete_all_feedback(conn) -> None:
    conn.execute("DELETE FROM feedback")
    conn.commit()

def delete_all_data(conn) -> None:
    conn.execute("DELETE FROM feedback")
    conn.execute("DELETE FROM messages")
    conn.execute("DELETE FROM conversations")
    conn.execute("DELETE FROM saved_prompts")
    conn.commit()

