import sqlite3
import hashlib

DB = "bot.db"


def init_db():
    with sqlite3.connect(DB) as con:
        cur = con.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER,
            queue TEXT,
            last_hash TEXT,
            PRIMARY KEY (user_id, queue)
        )
        """)

        con.commit()


def add_user(user_id: int):
    with sqlite3.connect(DB) as con:
        con.execute(
            "INSERT OR IGNORE INTO users(user_id) VALUES (?)",
            (user_id,)
        )


def is_allowed(user_id: int) -> bool:
    return True  # 🔒 якщо буде whitelist — зробимо


def save_subscription(user_id: int, queue: str):
    with sqlite3.connect(DB) as con:
        con.execute("""
        INSERT OR IGNORE INTO subscriptions (user_id, queue, last_hash)
        VALUES (?, ?, '')
        """, (user_id, queue))


def get_subscriptions():
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("""
        SELECT user_id, queue, last_hash FROM subscriptions
        """)
        return cur.fetchall()


def update_hash(user_id: int, queue: str, text: str):
    h = hashlib.sha256(text.encode()).hexdigest()

    with sqlite3.connect(DB) as con:
        con.execute("""
        UPDATE subscriptions
        SET last_hash = ?
        WHERE user_id = ? AND queue = ?
        """, (h, user_id, queue))

    return h
