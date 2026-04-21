from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import settings
from app.models import repository
from app.schemas import ExportRequest, ExportStatusResponse, JobResponse, JobStatusResponse, PreviewResponse, SegmentResponse
from app.services.analysis_service import run_uploaded_analysis
from app.services.export_service import run_export
from app.services.job_runner import job_runner

router = APIRouter(prefix="/api/v1")
_ALLOWED_UPLOAD_SUFFIXES = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".oga", ".opus", ".webm", ".mp4", ".mov"}


def _resolved_upload_suffix(filename: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    return suffix if suffix in _ALLOWED_UPLOAD_SUFFIXES else ".bin"


async def _save_upload(job_id: str, upload: UploadFile) -> Path:
    destination = settings.data_dir / "downloads" / f"{job_id}{_resolved_upload_suffix(upload.filename)}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        while chunk := await upload.read(1024 * 1024):
            handle.write(chunk)
    await upload.close()
    return destination


@router.post("/jobs", response_model=JobResponse)
async def create_upload_job(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    chapters_text: str | None = Form(None),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Upload must include a filename")
    if not (file.content_type or "").startswith(("audio/", "video/")) and Path(file.filename).suffix.lower() not in _ALLOWED_UPLOAD_SUFFIXES:
        raise HTTPException(status_code=400, detail="Unsupported upload type")

    job = repository.create_job("analyze")
    destination = await _save_upload(job["id"], file)
    display_title = (title or Path(file.filename).stem).strip() or Path(file.filename).stem
    resolved_chapters = (chapters_text or "").strip() or None
    job_runner.submit(run_uploaded_analysis, job["id"], str(destination), display_title, resolved_chapters)
    return JobResponse(jobId=job["id"], status=job["status"])


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str):
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(**job)


@router.get("/jobs/{job_id}/preview", response_model=PreviewResponse)
def get_preview(job_id: str):
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] not in ("preview_ready", "completed"):
        raise HTTPException(status_code=409, detail="Preview not ready")

    video = repository.get_video_by_job(job_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    segments = repository.list_segments(job_id)
    formatted = [
        SegmentResponse(
            index=row["idx"],
            startSec=row["start_sec"],
            endSec=row["end_sec"],
            name=row["title"],
            strategy=row["strategy"],
            confidence=row["confidence"],
        )
        for row in segments
    ]

    return PreviewResponse(
        video={
            "title": video.get("title"),
            "durationSec": video.get("duration_sec"),
        },
        segments=formatted,
    )


@router.post("/jobs/{job_id}/export", response_model=ExportStatusResponse)
def create_export(job_id: str, payload: ExportRequest):
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    segments = repository.list_segments(job_id)
    if not segments:
        raise HTTPException(status_code=409, detail="No segments to export")

    if payload.names:
        if len(payload.names) != len(segments):
            raise HTTPException(status_code=400, detail="names must match segment count")
        renamed_segments = []
        for row, new_name in zip(segments, payload.names):
            renamed_segments.append(
                {
                    "index": row["idx"],
                    "start_sec": row["start_sec"],
                    "end_sec": row["end_sec"],
                    "title": new_name.strip() or row["title"],
                    "strategy": row["strategy"],
                    "confidence": row["confidence"],
                }
            )
        video = repository.get_video_by_job(job_id)
        if video:
            repository.replace_segments(job_id, video["id"], renamed_segments)

    video = repository.get_video_by_job(job_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video record missing")

    export_row = repository.create_export(job_id=job_id, video_id=video["id"])
    job_runner.submit(run_export, export_row["id"])
    return ExportStatusResponse(
        exportId=export_row["id"],
        status=export_row["status"],
        zipPath=None,
        csvPath=None,
        txtPath=None,
        error=None,
    )


@router.get("/jobs/{job_id}/export", response_model=ExportStatusResponse)
def get_export_for_job(job_id: str):
    export_row = repository.get_export_by_job(job_id)
    if not export_row:
        raise HTTPException(status_code=404, detail="Export not found")

    return ExportStatusResponse(
        exportId=export_row["id"],
        status=export_row["status"],
        zipPath=export_row.get("zip_path"),
        csvPath=export_row.get("csv_path"),
        txtPath=export_row.get("txt_path"),
        error=export_row.get("error"),
    )


@router.get("/exports/{export_id}/download")
def download_export(export_id: str):
    export_row = repository.get_export(export_id)
    if not export_row:
        raise HTTPException(status_code=404, detail="Export not found")
    if export_row.get("status") != "completed" or not export_row.get("zip_path"):
        raise HTTPException(status_code=409, detail="Export is not ready")

    zip_path = Path(export_row["zip_path"])
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Zip artifact missing")
    return FileResponse(path=str(zip_path), filename=zip_path.name, media_type="application/zip")
