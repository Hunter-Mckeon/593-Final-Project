# init_db.py
import sqlite3
import os

DB_PATH = "example.db"

def init_db():
    # Remove old DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Enforce foreign keys
    cur.execute("PRAGMA foreign_keys = ON;")

    sql = """
    CREATE TABLE users (
        id      INTEGER PRIMARY KEY,
        email   TEXT NOT NULL UNIQUE,
        name    TEXT NOT NULL
    );

    CREATE TABLE projects (
        id        INTEGER PRIMARY KEY,
        owner_id  INTEGER NOT NULL,
        title     TEXT NOT NULL,
        FOREIGN KEY (owner_id) REFERENCES users(id)
    );

    CREATE TABLE project_members (
        project_id INTEGER NOT NULL,
        user_id    INTEGER NOT NULL,
        role       TEXT NOT NULL,
        PRIMARY KEY (project_id, user_id),
        FOREIGN KEY (project_id) REFERENCES projects(id),
        FOREIGN KEY (user_id)    REFERENCES users(id)
    );

    CREATE TABLE tasks (
        id         INTEGER PRIMARY KEY,
        project_id INTEGER NOT NULL,
        title      TEXT NOT NULL,
        done       INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    );

    CREATE TABLE profile_notes (
        id      INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        note    TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE login_events (
        id      INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        ts      TEXT NOT NULL,
        ip      TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    """

    cur.executescript(sql)

    conn.commit()
    conn.close()
    print("Database initialized successfully:", DB_PATH)

if __name__ == "__main__":
    init_db()
