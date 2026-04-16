import subprocess
from pathlib import Path

from audio_engine.segment_fallback import probe_duration


def sanitize_filename(value: str) -> str:
    safe = "".join(ch for ch in value if ch.isalnum() or ch in ("-", "_", " ")).strip()
    return safe.replace(" ", "_")[:80] or "segment"


def split_audio(source_path: Path, segments: list[dict], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    duration = int(probe_duration(source_path))
    clips: list[Path] = []

    for segment in segments:
        idx = segment["idx"]
        start = int(segment["start_sec"])
        end = segment.get("end_sec")
        if end is None:
            end = duration

        clip_name = f"{idx + 1:03d}_{sanitize_filename(segment['title'])}.mp3"
        clip_path = output_dir / clip_name

        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(source_path),
                "-ss",
                str(start),
                "-to",
                str(int(end)),
                "-vn",
                "-c:a",
                "libmp3lame",
                "-q:a",
                "2",
                str(clip_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"ffmpeg split failed for {clip_name}")
        clips.append(clip_path)

    return clips
