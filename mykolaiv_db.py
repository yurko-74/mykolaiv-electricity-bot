import sqlite3

DB_NAME = "bot.db"


def get_conn():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # користувачі
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    """)

    # черги користувачів
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_queues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            queue TEXT,
            UNIQUE(user_id, queue)
        )
    """)

    conn.commit()
    conn.close()


# ---------- USERS ----------

def add_user(user_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )

    conn.commit()
    conn.close()


def is_allowed(user_id: int) -> bool:
    # поки дозволяємо всім
    return True


# ---------- QUEUES ----------

def add_queue(user_id: int, queue: str) -> bool:
    """
    Додає чергу користувачу.
    Повертає False, якщо вже 2 черги
    """
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM user_queues WHERE user_id = ?",
        (user_id,)
    )
    count = cur.fetchone()[0]

    if count >= 2:
        conn.close()
        return False

    cur.execute(
        "INSERT OR IGNORE INTO user_queues (user_id, queue) VALUES (?, ?)",
        (user_id, queue)
    )

    conn.commit()
    conn.close()
    return True


def get_user_queues(user_id: int) -> list[str]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT queue FROM user_queues WHERE user_id = ?",
        (user_id,)
    )

    rows = cur.fetchall()
    conn.close()

    return [r[0] for r in rows]


def clear_user_queues(user_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM user_queues WHERE user_id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()


def get_all_users_with_queues() -> dict:
    """
    { user_id: [queue1, queue2] }
    """
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, queue
        FROM user_queues
        ORDER BY user_id
    """)

    rows = cur.fetchall()
    conn.close()

    result = {}
    for user_id, queue in rows:
        result.setdefault(user_id, []).append(queue)

    return result
