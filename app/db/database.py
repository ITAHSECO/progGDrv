import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gdrive_scheduler.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            source_path TEXT NOT NULL,
            drive_folder_id TEXT DEFAULT '',
            active INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL UNIQUE,
            hour_start INTEGER DEFAULT 0,
            minute_start INTEGER DEFAULT 0,
            hour_end INTEGER DEFAULT 23,
            minute_end INTEGER DEFAULT 59,
            interval_minutes INTEGER DEFAULT 120,
            mon INTEGER DEFAULT 1,
            tue INTEGER DEFAULT 1,
            wed INTEGER DEFAULT 1,
            thu INTEGER DEFAULT 1,
            fri INTEGER DEFAULT 1,
            sat INTEGER DEFAULT 0,
            sun INTEGER DEFAULT 0,
            FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS upload_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            upload_time TEXT DEFAULT (datetime('now','localtime')),
            status TEXT NOT NULL,
            message TEXT DEFAULT '',
            file_size INTEGER DEFAULT 0,
            FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
        )
    """)

    _migrate_schema(cursor)
    conn.commit()
    conn.close()


def _migrate_schema(cursor):
    cursor.execute("PRAGMA table_info(schedules)")
    columns = {row[1] for row in cursor.fetchall()}

    if "minute_start" not in columns:
        cursor.execute("ALTER TABLE schedules ADD COLUMN minute_start INTEGER DEFAULT 0")
    if "minute_end" not in columns:
        cursor.execute("ALTER TABLE schedules ADD COLUMN minute_end INTEGER DEFAULT 59")
    if "interval_minutes" not in columns:
        cursor.execute("ALTER TABLE schedules ADD COLUMN interval_minutes INTEGER DEFAULT 120")
        cursor.execute("UPDATE schedules SET interval_minutes = CAST(interval_hours * 60 AS INTEGER) WHERE interval_minutes = 120")
        cursor.execute("ALTER TABLE schedules DROP COLUMN interval_hours")


def add_file(name, source_path, drive_folder_id=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO files (name, source_path, drive_folder_id) VALUES (?, ?, ?)",
        (name, source_path, drive_folder_id),
    )
    file_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO schedules (file_id) VALUES (?)", (file_id,)
    )
    conn.commit()
    conn.close()
    return file_id


def update_file(file_id, name, source_path, drive_folder_id):
    conn = get_connection()
    conn.execute(
        "UPDATE files SET name=?, source_path=?, drive_folder_id=? WHERE id=?",
        (name, source_path, drive_folder_id, file_id),
    )
    conn.commit()
    conn.close()


def delete_file(file_id):
    conn = get_connection()
    conn.execute("DELETE FROM files WHERE id=?", (file_id,))
    conn.commit()
    conn.close()


def set_file_active(file_id, active):
    conn = get_connection()
    conn.execute("UPDATE files SET active=? WHERE id=?", (int(active), file_id))
    conn.commit()
    conn.close()


def get_file(file_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM files WHERE id=?", (file_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_files():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM files ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_active_files():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM files WHERE active=1 ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_schedule(file_id, hour_start, minute_start, hour_end, minute_end,
                    interval_minutes, mon, tue, wed, thu, fri, sat, sun):
    conn = get_connection()
    conn.execute("""
        UPDATE schedules
        SET hour_start=?, minute_start=?, hour_end=?, minute_end=?,
            interval_minutes=?,
            mon=?, tue=?, wed=?, thu=?, fri=?, sat=?, sun=?
        WHERE file_id=?
    """, (hour_start, minute_start, hour_end, minute_end, interval_minutes,
          int(mon), int(tue), int(wed), int(thu), int(fri), int(sat), int(sun),
          file_id))
    conn.commit()
    conn.close()


def get_schedule(file_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM schedules WHERE file_id=?", (file_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_history(file_id, status, message="", file_size=0):
    conn = get_connection()
    conn.execute(
        "INSERT INTO upload_history (file_id, status, message, file_size) VALUES (?, ?, ?, ?)",
        (file_id, status, message, file_size),
    )
    conn.commit()
    conn.close()


def get_history(file_id=None, limit=500):
    conn = get_connection()
    if file_id:
        rows = conn.execute(
            "SELECT h.*, f.name as file_name FROM upload_history h "
            "JOIN files f ON h.file_id=f.id WHERE h.file_id=? ORDER BY h.upload_time DESC LIMIT ?",
            (file_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT h.*, f.name as file_name FROM upload_history h "
            "JOIN files f ON h.file_id=f.id ORDER BY h.upload_time DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_history():
    conn = get_connection()
    conn.execute("DELETE FROM upload_history")
    conn.commit()
    conn.close()
