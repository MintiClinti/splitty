#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from audio_engine.chapters import extract_chapters_from_description  # noqa: E402


def _sanitize_filename(value: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", value).strip()
    return cleaned[:120] or "download"


def _format_timestamp(total_seconds: int) -> str:
    hours, remainder = divmod(max(0, total_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def _run_yt_dlp(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["yt-dlp", "--no-playlist", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _load_metadata(url: str) -> dict:
    result = _run_yt_dlp("--dump-single-json", "--skip-download", url)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "yt-dlp metadata fetch failed")
    return json.loads(result.stdout)


def _write_chapters_file(base_path: Path, metadata: dict) -> Path | None:
    chapters = metadata.get("chapters") or []
    lines: list[str] = []
    if chapters:
        for chapter in chapters:
            start = int(chapter.get("start_time") or 0)
            title = (chapter.get("title") or "").strip() or f"Segment {len(lines) + 1}"
            lines.append(f"{_format_timestamp(start)} {title}")
    else:
        description = metadata.get("description") or ""
        for start, title in extract_chapters_from_description(description):
            lines.append(f"{start} {title}")

    if not lines:
        return None

    chapters_path = base_path.with_suffix(".chapters.txt")
    chapters_path.write_text("\n".join(lines) + "\n")
    return chapters_path


def download_audio(url: str, output_dir: Path) -> tuple[Path, Path | None]:
    metadata = _load_metadata(url)
    stem = _sanitize_filename(f"{metadata.get('title') or metadata.get('id') or 'download'} [{metadata.get('id') or 'audio'}]")
    output_template = output_dir / f"{stem}.%(ext)s"

    result = _run_yt_dlp("-f", "bestaudio/best", "-x", "--audio-format", "mp3", "-o", str(output_template), url)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "yt-dlp download failed")

    matches = sorted(output_dir.glob(f"{stem}.*"))
    audio_path = next((path for path in matches if path.suffix != ".txt"), None)
    if audio_path is None:
        raise RuntimeError("Could not locate downloaded audio file")

    chapters_path = _write_chapters_file(audio_path, metadata)
    return audio_path, chapters_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Download YouTube audio locally for Splitty uploads.")
    parser.add_argument("url", help="YouTube URL to download locally")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=str(ROOT / "local_downloads"),
        help="Directory to place the downloaded audio and chapter sidecar",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        audio_path, chapters_path = download_audio(args.url, output_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"Download failed: {exc}", file=sys.stderr)
        return 1

    print(f"Audio: {audio_path}")
    if chapters_path:
        print(f"Chapters: {chapters_path}")
        print("Upload both files in Splitty to keep chapter-based splits.")
    else:
        print("No chapter sidecar was generated; Splitty will fall back to audio-based segmentation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
