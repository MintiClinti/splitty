from pathlib import Path


def cleanup_empty_dirs(base_path: Path) -> None:
    if not base_path.exists():
        return
    for child in base_path.iterdir():
        if child.is_dir():
            cleanup_empty_dirs(child)
            if not any(child.iterdir()):
                child.rmdir()
