from pathlib import Path

from app.core.config import settings
from app.models import repository
from audio_engine.chapters import chapters_to_segments, extract_chapters_from_description, extract_chapters_from_metadata
from audio_engine.postprocess import enforce_min_lengths
from audio_engine.segment_fallback import detect_fallback_segments
from audio_engine.youtube import download_audio, fetch_metadata, validate_youtube_url


def run_analysis(job_id: str, youtube_url: str) -> None:
    try:
        if not validate_youtube_url(youtube_url):
            raise ValueError("Invalid YouTube URL format")

        repository.update_job(job_id, status="running", stage="fetching_metadata", progress=10)
        metadata = fetch_metadata(youtube_url)

        repository.update_job(job_id, stage="downloading_audio", progress=30)
        source_path = download_audio(youtube_url, settings.data_dir / "downloads", file_stem=job_id)

        video = repository.create_video(job_id=job_id, youtube_url=youtube_url, metadata=metadata, source_path=str(source_path))

        repository.update_job(job_id, stage="segmenting", progress=55)
        duration_sec = metadata.get("duration")
        chapter_segments = extract_chapters_from_metadata(metadata)
        if not chapter_segments:
            description = metadata.get("description") or ""
            chapter_segments = chapters_to_segments(extract_chapters_from_description(description), duration_sec=duration_sec)

        chosen = chapter_segments if chapter_segments else detect_fallback_segments(Path(source_path), duration_sec)
        cleaned = enforce_min_lengths(
            chosen,
            min_length_sec=settings.min_segment_length_sec,
            merge_threshold_sec=settings.merge_threshold_sec,
            duration_sec=duration_sec,
        )

        repository.replace_segments(job_id, video["id"], cleaned)
        repository.update_job(job_id, status="preview_ready", stage="ready_for_preview", progress=100)
    except Exception as exc:  # noqa: BLE001
        repository.update_job(job_id, status="failed", stage="failed", error=str(exc))
