from app.core.config import settings


def ensure_runtime_dirs() -> None:
    for child in ("downloads", "segments", "exports", "tmp", "yt-oauth"):
        (settings.data_dir / child).mkdir(parents=True, exist_ok=True)
