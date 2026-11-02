
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "recruitment.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interviewer_availability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interviewer TEXT NOT NULL,
                slot_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Free'
                    CHECK(status IN ('Free', 'Busy', 'Booked'))
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_name TEXT NOT NULL,
                candidate_email TEXT,
                interviewer TEXT NOT NULL,
                slot_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Scheduled',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(interviewer, slot_date, start_time)
            )
        """)


def add_availability(
    interviewer, slot_date, start_time, end_time, status="Free"
):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO interviewer_availability
            (interviewer, slot_date, start_time, end_time, status)
            VALUES (?, ?, ?, ?, ?)
        """, (interviewer, slot_date, start_time, end_time, status))


def get_interviewers():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT DISTINCT interviewer
            FROM interviewer_availability
            ORDER BY interviewer
        """).fetchall()

    return [row["interviewer"] for row in rows]


def get_available_slots(interviewer, slot_date):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT a.start_time, a.end_time
            FROM interviewer_availability AS a
            WHERE a.interviewer = ?
              AND a.slot_date = ?
              AND a.status = 'Free'
              AND NOT EXISTS (
                  SELECT 1
                  FROM interviews AS i
                  WHERE i.interviewer = a.interviewer
                    AND i.slot_date = a.slot_date
                    AND i.status = 'Scheduled'
                    AND a.start_time < i.end_time
                    AND a.end_time > i.start_time
              )
            ORDER BY a.start_time
        """, (interviewer, slot_date)).fetchall()

    return [dict(row) for row in rows]


def book_interview(
    candidate_name, candidate_email, interviewer,
    slot_date, start_time, end_time
):
    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")

        slot = conn.execute("""
            SELECT id
            FROM interviewer_availability
            WHERE interviewer = ?
              AND slot_date = ?
              AND start_time <= ?
              AND end_time >= ?
              AND status = 'Free'
            LIMIT 1
        """, (interviewer, slot_date, start_time, end_time)).fetchone()

        if not slot:
            raise ValueError(
                "This time slot is no longer available. Please choose another."
            )

        conflict = conn.execute("""
            SELECT id
            FROM interviews
            WHERE interviewer = ?
              AND slot_date = ?
              AND status = 'Scheduled'
              AND start_time < ?
              AND end_time > ?
        """, (interviewer, slot_date, end_time, start_time)).fetchone()

        if conflict:
            raise ValueError(
                "Scheduling conflict detected. Please choose another slot."
            )

        conn.execute("""
            INSERT INTO interviews
            (candidate_name, candidate_email, interviewer,
             slot_date, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            candidate_name, candidate_email, interviewer,
            slot_date, start_time, end_time
        ))


def get_scheduled_interviews():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT candidate_name, candidate_email, interviewer,
                   slot_date, start_time, end_time, status
            FROM interviews
            ORDER BY slot_date, start_time
        """).fetchall()

    return [dict(row) for row in rows]



def seed_sample_availability():
    """Insert demo slots only when the calendar is empty."""

    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM interviewer_availability"
        ).fetchone()[0]

    if count > 0:
        return

    sample_slots = [
        ("Dr. Sharma", "2026-10-20", "09:00", "09:30", "Busy"),
        ("Dr. Sharma", "2026-10-20", "09:30", "10:00", "Free"),
        ("Dr. Sharma", "2026-10-20", "10:00", "10:30", "Free"),
        ("Dr. Sharma", "2026-10-20", "10:30", "11:00", "Busy"),
        ("Dr. Sharma", "2026-10-20", "11:00", "11:30", "Free"),
        ("Dr. Priya", "2026-10-20", "09:00", "09:30", "Free"),
        ("Dr. Priya", "2026-10-20", "09:30", "10:00", "Busy"),
        ("Dr. Priya", "2026-10-20", "10:00", "10:30", "Free"),
    ]

    with get_connection() as conn:
        conn.executemany("""
            INSERT INTO interviewer_availability
            (interviewer, slot_date, start_time, end_time, status)
            VALUES (?, ?, ?, ?, ?)
        """, sample_slots)
