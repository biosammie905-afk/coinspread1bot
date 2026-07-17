import sqlite3
from contextlib import contextmanager
from config import DB_PATH


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                chat_id INTEGER PRIMARY KEY,
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS seen_items (
                source TEXT NOT NULL,
                item_id TEXT NOT NULL,
                seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source, item_id)
            )
        """)


def add_subscriber(chat_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)", (chat_id,)
        )


def remove_subscriber(chat_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))


def get_subscribers():
    with get_conn() as conn:
        rows = conn.execute("SELECT chat_id FROM subscribers").fetchall()
        return [r[0] for r in rows]


def is_seen(source: str, item_id: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM seen_items WHERE source = ? AND item_id = ?",
            (source, item_id),
        ).fetchone()
        return row is not None


def mark_seen(source: str, item_id: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen_items (source, item_id) VALUES (?, ?)",
            (source, item_id),
        )
