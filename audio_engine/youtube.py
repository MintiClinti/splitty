import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlparse

YOUTUBE_PATTERN = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[A-Za-z0-9_-]{6,}"
)

_YT_DLP_COMMON_ARGS = [
    "--no-playlist",
    "--extractor-args", "youtube:player_client=android",
]


def _auth_args() -> list[str]:
    """Return yt-dlp auth flags based on available credentials."""
    cookies_path = os.environ.get("YT_COOKIES_PATH", "")
    if cookies_path and Path(cookies_path).is_file():
        return ["--cookies", cookies_path]
    token_dir = Path(os.environ.get("YT_TOKEN_DIR", "/app/backend/data/yt-oauth"))
    token_dir.mkdir(parents=True, exist_ok=True)
    return [
        "--username", "oauth2",
        "--password", "",
        "--cache-dir", str(token_dir),
    ]


def validate_youtube_url(url: str) -> bool:
    return bool(YOUTUBE_PATTERN.match(url.strip()))


def _clean_url(url: str) -> str:
    """Strip playlist/radio/timestamp params so yt-dlp treats it as a single video."""
    parsed = urlparse(url.strip())
    params = parse_qs(parsed.query)
    video_id = params.get("v", [None])[0]
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return url.strip()


def _extract_error(stderr: str) -> str:
    """Return only the first real ERROR line from yt-dlp stderr."""
    for line in stderr.splitlines():
        if line.strip().startswith("ERROR"):
            return line.strip()
    return stderr.strip()[:300] or "yt-dlp failed (unknown reason)"


def fetch_metadata(url: str) -> dict:
    clean = _clean_url(url)
    result = subprocess.run(
        ["yt-dlp", *_YT_DLP_COMMON_ARGS, *_auth_args(), "--dump-single-json", "--skip-download", clean],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(_extract_error(result.stderr))
    return json.loads(result.stdout)


def download_audio(url: str, output_dir: Path, file_stem: str) -> Path:
    clean = _clean_url(url)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = output_dir / f"{file_stem}.%(ext)s"
    result = subprocess.run(
        [
            "yt-dlp",
            *_YT_DLP_COMMON_ARGS,
            *_auth_args(),
            "-x",
            "--audio-format", "mp3",
            "-o", str(output_template),
            clean,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(_extract_error(result.stderr))

    matches = sorted(output_dir.glob(f"{file_stem}.*"))
    if not matches:
        raise RuntimeError("Could not locate downloaded audio output")
    return matches[0]
