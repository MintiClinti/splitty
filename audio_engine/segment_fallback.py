import subprocess
from pathlib import Path


def _detect_silence_boundaries(audio_path: Path, noise_db: int = -25, min_silence_sec: float = 0.7) -> list[int]:
    cmd = [
        "ffmpeg",
        "-i",
        str(audio_path),
        "-af",
        f"silencedetect=noise={noise_db}dB:d={min_silence_sec}",
        "-f",
        "null",
        "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    boundaries: list[int] = []
    for line in result.stderr.splitlines():
        if "silence_end:" in line:
            try:
                fragment = line.split("silence_end:")[1].split("|")[0].strip()
                boundaries.append(int(float(fragment)))
            except (ValueError, IndexError):
                continue
    return sorted(set(boundaries))


def _merge_short_spans(
    spans: list[tuple[int, int | None]],
    min_duration_sec: int = 60,
) -> list[tuple[int, int | None]]:
    if not spans:
        return spans

    merged: list[tuple[int, int | None]] = [spans[0]]
    for start, end in spans[1:]:
        prev_start, prev_end = merged[-1]
        effective_end = end if end is not None else start
        duration = effective_end - start
        if duration < min_duration_sec:
            merged[-1] = (prev_start, end)
        else:
            merged.append((start, end))
    return merged


def _uniform_segments(duration_sec: int, step_sec: int = 180) -> list[tuple[int, int | None]]:
    spans = []
    start = 0
    while start < duration_sec:
        end = min(start + step_sec, duration_sec)
        spans.append((start, end if end < duration_sec else None))
        start += step_sec
    return spans


def probe_duration(audio_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe failed")
    return float(result.stdout.strip())


def detect_fallback_segments(audio_path: Path, duration_sec: int | None) -> list[dict]:
    if not duration_sec or duration_sec <= 0:
        try:
            duration_sec = int(probe_duration(audio_path))
        except RuntimeError:
            duration_sec = 1800

    boundaries = [0]
    boundaries.extend(_detect_silence_boundaries(audio_path))
    boundaries = sorted(set([point for point in boundaries if point < duration_sec]))

    if len(boundaries) < 2:
        spans = _uniform_segments(duration_sec)
    else:
        spans = []
        for idx, start in enumerate(boundaries):
            end = boundaries[idx + 1] if idx + 1 < len(boundaries) else duration_sec
            if end > start:
                spans.append((start, end if end < duration_sec else None))
        spans = _merge_short_spans(spans)

    segments: list[dict] = []
    for index, (start, end) in enumerate(spans):
        segments.append(
            {
                "index": index,
                "start_sec": int(start),
                "end_sec": int(end) if end is not None else None,
                "title": f"Segment {index + 1}",
                "strategy": "fallback",
                "confidence": 0.5,
            }
        )
    return segments
