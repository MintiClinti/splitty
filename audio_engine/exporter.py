import csv
import zipfile
from pathlib import Path


def write_csv_manifest(segments: list[dict], target_path: Path) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["index", "start_sec", "end_sec", "title", "strategy"])
        for segment in segments:
            writer.writerow([
                segment["idx"],
                segment["start_sec"],
                segment.get("end_sec"),
                segment["title"],
                segment["strategy"],
            ])
    return target_path


def write_txt_manifest(segments: list[dict], target_path: Path) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as handle:
        for segment in segments:
            end = segment.get("end_sec")
            handle.write(f"{segment['idx'] + 1}. {segment['start_sec']} -> {end if end is not None else 'END'} | {segment['title']}\n")
    return target_path


def build_zip(clips: list[Path], csv_path: Path, txt_path: Path, zip_path: Path) -> Path:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for clip in clips:
            archive.write(clip, arcname=f"audio/{clip.name}")
        archive.write(csv_path, arcname=csv_path.name)
        archive.write(txt_path, arcname=txt_path.name)
    return zip_path
