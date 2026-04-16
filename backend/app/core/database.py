import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from app.core.config import settings


def now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


@contextmanager
def get_conn():
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = dict_factory
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                progress INTEGER NOT NULL,
                stage TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                youtube_url TEXT NOT NULL,
                youtube_video_id TEXT,
                title TEXT,
                duration_sec INTEGER,
                source_path TEXT,
                metadata_json TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS segments (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                idx INTEGER NOT NULL,
                start_sec INTEGER NOT NULL,
                end_sec INTEGER,
                title TEXT NOT NULL,
                strategy TEXT NOT NULL,
                confidence REAL,
                clip_path TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS exports (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                status TEXT NOT NULL,
                zip_path TEXT,
                csv_path TEXT,
                txt_path TEXT,
                segment_count INTEGER,
                total_duration_sec INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                error TEXT
            )
            """
        )
