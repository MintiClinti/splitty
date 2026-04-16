import re

ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\ufeff]")


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return ZERO_WIDTH.sub("", text)


def parse_time_to_seconds(value: str) -> int:
    parts = [int(x) for x in value.split(":")]
    if len(parts) == 2:
        minutes, seconds = parts
        return minutes * 60 + seconds
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return hours * 3600 + minutes * 60 + seconds
    raise ValueError(f"Invalid timestamp: {value}")


def extract_chapters_from_description(description: str) -> list[tuple[str, str]]:
    text = normalize(description)
    pat_range = re.compile(
        r"^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—]\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—]\s*(.+?)\s*$"
    )
    pat_start_title = re.compile(r"^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+?)\s*$")

    chapters: list[tuple[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        range_match = pat_range.match(line)
        if range_match:
            chapters.append((range_match.group(1), range_match.group(3).strip()))
            continue

        start_match = pat_start_title.match(line)
        if start_match:
            chapters.append((start_match.group(1), start_match.group(2).strip()))

    return chapters


def chapters_to_segments(chapters: list[tuple[str, str]], duration_sec: int | None) -> list[dict]:
    if not chapters:
        return []

    resolved: list[dict] = []
    for i, (start, title) in enumerate(chapters):
        start_sec = parse_time_to_seconds(start)
        end_sec = parse_time_to_seconds(chapters[i + 1][0]) if i + 1 < len(chapters) else duration_sec
        resolved.append(
            {
                "index": i,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "title": title or f"Segment {i + 1}",
                "strategy": "chapter",
                "confidence": 1.0,
            }
        )
    return resolved


def extract_chapters_from_metadata(metadata: dict) -> list[dict]:
    chapters = metadata.get("chapters") or []
    normalized: list[dict] = []
    for i, chapter in enumerate(chapters):
        start = int(chapter.get("start_time", 0))
        end = chapter.get("end_time")
        normalized.append(
            {
                "index": i,
                "start_sec": start,
                "end_sec": int(end) if end is not None else None,
                "title": chapter.get("title") or f"Segment {i + 1}",
                "strategy": "chapter",
                "confidence": 1.0,
            }
        )
    return normalized
