import json
import uuid
from typing import Any

from app.core.database import get_conn, now_iso


def create_job(job_type: str) -> dict[str, Any]:
    job = {
        "id": str(uuid.uuid4()),
        "type": job_type,
        "status": "pending",
        "progress": 0,
        "stage": "queued",
        "error": None,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO jobs (id, type, status, progress, stage, error, created_at, updated_at)
            VALUES (:id, :type, :status, :progress, :stage, :error, :created_at, :updated_at)
            """,
            job,
        )
    return job


def update_job(job_id: str, **fields) -> None:
    if not fields:
        return
    fields["updated_at"] = now_iso()
    assignments = ", ".join([f"{key} = :{key}" for key in fields])
    fields["job_id"] = job_id
    with get_conn() as conn:
        conn.execute(f"UPDATE jobs SET {assignments} WHERE id = :job_id", fields)


def get_job(job_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()


def create_video(job_id: str, metadata: dict[str, Any], source_path: str | None, source_ref: str = "") -> dict[str, Any]:
    video = {
        "id": str(uuid.uuid4()),
        "job_id": job_id,
        "youtube_url": source_ref,
        "youtube_video_id": metadata.get("id"),
        "title": metadata.get("title"),
        "duration_sec": metadata.get("duration"),
        "source_path": source_path,
        "metadata_json": json.dumps(metadata),
        "created_at": now_iso(),
    }
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO videos (id, job_id, youtube_url, youtube_video_id, title, duration_sec, source_path, metadata_json, created_at)
            VALUES (:id, :job_id, :youtube_url, :youtube_video_id, :title, :duration_sec, :source_path, :metadata_json, :created_at)
            """,
            video,
        )
    return video


def get_video_by_job(job_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM videos WHERE job_id = ?", (job_id,)).fetchone()


def replace_segments(job_id: str, video_id: str, segments: list[dict[str, Any]]) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM segments WHERE job_id = ?", (job_id,))
        for segment in segments:
            payload = {
                "id": str(uuid.uuid4()),
                "job_id": job_id,
                "video_id": video_id,
                "idx": segment["index"],
                "start_sec": segment["start_sec"],
                "end_sec": segment.get("end_sec"),
                "title": segment["title"],
                "strategy": segment["strategy"],
                "confidence": segment.get("confidence"),
                "clip_path": segment.get("clip_path"),
            }
            conn.execute(
                """
                INSERT INTO segments (id, job_id, video_id, idx, start_sec, end_sec, title, strategy, confidence, clip_path)
                VALUES (:id, :job_id, :video_id, :idx, :start_sec, :end_sec, :title, :strategy, :confidence, :clip_path)
                """,
                payload,
            )


def list_segments(job_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM segments WHERE job_id = ? ORDER BY idx ASC", (job_id,)).fetchall()


def create_export(job_id: str, video_id: str) -> dict[str, Any]:
    export_row = {
        "id": str(uuid.uuid4()),
        "job_id": job_id,
        "video_id": video_id,
        "status": "pending",
        "zip_path": None,
        "csv_path": None,
        "txt_path": None,
        "segment_count": None,
        "total_duration_sec": None,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "error": None,
    }
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO exports (id, job_id, video_id, status, zip_path, csv_path, txt_path, segment_count, total_duration_sec, created_at, updated_at, error)
            VALUES (:id, :job_id, :video_id, :status, :zip_path, :csv_path, :txt_path, :segment_count, :total_duration_sec, :created_at, :updated_at, :error)
            """,
            export_row,
        )
    return export_row


def update_export(export_id: str, **fields) -> None:
    if not fields:
        return
    fields["updated_at"] = now_iso()
    assignments = ", ".join([f"{key} = :{key}" for key in fields])
    fields["export_id"] = export_id
    with get_conn() as conn:
        conn.execute(f"UPDATE exports SET {assignments} WHERE id = :export_id", fields)


def get_export(export_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM exports WHERE id = ?", (export_id,)).fetchone()


def get_export_by_job(job_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM exports WHERE job_id = ? ORDER BY created_at DESC LIMIT 1", (job_id,)
        ).fetchone()
