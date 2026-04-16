from pathlib import Path

from app.core.config import settings
from app.models import repository
from audio_engine.exporter import build_zip, write_csv_manifest, write_txt_manifest
from audio_engine.splitter import split_audio


def run_export(export_id: str) -> None:
    export_row = repository.get_export(export_id)
    if not export_row:
        return

    try:
        repository.update_export(export_id, status="running")
        job_id = export_row["job_id"]
        video = repository.get_video_by_job(job_id)
        if not video:
            raise RuntimeError("Video record missing for export")

        segments = repository.list_segments(job_id)
        if not segments:
            raise RuntimeError("No segments available to export")

        source_path = video.get("source_path")
        if not source_path:
            raise RuntimeError("Source audio path is missing")

        clip_dir = settings.data_dir / "segments" / export_id
        manifest_dir = settings.data_dir / "tmp" / export_id

        clips = split_audio(Path(source_path), segments, clip_dir)
        csv_path = write_csv_manifest(segments, manifest_dir / "timestamps.csv")
        txt_path = write_txt_manifest(segments, manifest_dir / "timestamps.txt")
        zip_path = build_zip(clips, csv_path, txt_path, settings.data_dir / "exports" / f"{export_id}.zip")

        total_duration = 0
        for segment in segments:
            end = segment.get("end_sec")
            if end is not None:
                total_duration += max(0, int(end) - int(segment["start_sec"]))

        repository.update_export(
            export_id,
            status="completed",
            zip_path=str(zip_path),
            csv_path=str(csv_path),
            txt_path=str(txt_path),
            segment_count=len(segments),
            total_duration_sec=total_duration,
        )
    except Exception as exc:  # noqa: BLE001
        repository.update_export(export_id, status="failed", error=str(exc))
