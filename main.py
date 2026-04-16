import re
import subprocess

ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\ufeff]")

def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = ZERO_WIDTH.sub("", text)
    return text

def get_description(url: str) -> str:
    result = subprocess.run(
        ["yt-dlp", "--get-description", url],
        capture_output=True,
        text=True,
        check=False
    )
    return result.stdout or ""

def parse_time_to_seconds(t: str) -> int:
    parts = [int(x) for x in t.split(":")]
    if len(parts) == 2:      # MM:SS
        m, s = parts
        return 60*m + s
    elif len(parts) == 3:    # HH:MM:SS
        h, m, s = parts
        return 3600*h + 60*m + s
    else:
        raise ValueError(f"Bad timestamp: {t}")

def extract_chapters(description: str):
    """
    Returns list of (start_str, title) sorted by appearance.
    Supports:
      1) start - end - title
      2) start title
    """
    text = normalize(description)

    # Split into lines and parse line-by-line (less fragile than a big regex over the whole blob)
    chapters = []

    # A) "start - end - title" with -, – or —
    pat_range = re.compile(
        r"^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—]\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—]\s*(.+?)\s*$"
    )

    # B) "start title" (your Vietnam list)
    pat_start_title = re.compile(
        r"^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+?)\s*$"
    )

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        m = pat_range.match(line)
        if m:
            start, end, title = m.group(1), m.group(2), m.group(3).strip()
            chapters.append((start, title))
            # we ignore the provided `end` here; we'll compute ends from the next start for consistency
            continue

        m = pat_start_title.match(line)
        if m:
            start, title = m.group(1), m.group(2).strip()
            chapters.append((start, title))
            continue

    return chapters

def build_ranges(chapters):
    """
    chapters: list of (start_str, title)
    returns: list of (start_str, end_str|None, title)
    """
    ranges = []
    for i, (start, title) in enumerate(chapters):
        end = chapters[i+1][0] if i+1 < len(chapters) else None
        ranges.append((start, end, title))
    return ranges

def build_ranges_seconds(chapters):
    """
    returns (start_sec, end_sec|None, title) which is handy for slicing audio, etc.
    """
    out = []
    for i, (start, title) in enumerate(chapters):
        start_s = parse_time_to_seconds(start)
        end_s = parse_time_to_seconds(chapters[i+1][0]) if i+1 < len(chapters) else None
        out.append((start_s, end_s, title))
    return out

# Example usage on pasted text:
pasted = """00:00 Vở Kịch Của Em
03:52 Thu Cuối
01:01:58 Người Tính Duyên Trời

"""
already = 'https://youtu.be/oOydk6FXGwU?si=MmYlqRaFwEdwLk59'
already2 = 'https://youtu.be/Mn_voIPMe14?si=g7jHMz5z9-DCof1G'
x = get_description(already2)
chapters = extract_chapters(x)
print(build_ranges(chapters))