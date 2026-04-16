from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "Splitty API"
    app_version: str = "0.1.0"
    cors_origin: str = os.environ.get("CORS_ORIGIN", "http://localhost:5173")
    data_dir: Path = Path("data")
    db_path: Path = Path("data/splitty.db")
    min_segment_length_sec: int = 60
    merge_threshold_sec: int = 30
    max_workers: int = 2


settings = Settings()
