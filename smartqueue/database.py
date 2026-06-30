import sqlite3

def init_db():
    conn = sqlite3.connect("queue.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        location TEXT,
        number INTEGER,
        status TEXT DEFAULT 'waiting',
        created_at TEXT,
        served_at TEXT
    )
    """)

    conn.commit()
    conn.close()