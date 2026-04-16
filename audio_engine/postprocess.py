def enforce_min_lengths(
    segments: list[dict],
    min_length_sec: int,
    merge_threshold_sec: int,
    duration_sec: int | None,
) -> list[dict]:
    if not segments:
        return []

    normalized = [dict(item) for item in segments]
    merged: list[dict] = []
    for segment in normalized:
        if not merged:
            merged.append(segment)
            continue

        prev = merged[-1]
        prev_end = prev.get("end_sec") if prev.get("end_sec") is not None else duration_sec
        if prev_end is None:
            prev_end = segment["start_sec"]

        length = max(0, prev_end - prev["start_sec"])
        if length < merge_threshold_sec:
            prev["end_sec"] = segment.get("end_sec")
            prev["title"] = f"{prev['title']} + {segment['title']}"
        else:
            merged.append(segment)

    out: list[dict] = []
    for idx, segment in enumerate(merged):
        item = dict(segment)
        item["index"] = idx
        start = item["start_sec"]
        end = item.get("end_sec") if item.get("end_sec") is not None else duration_sec
        if end is not None and end - start < min_length_sec and out:
            out[-1]["end_sec"] = item.get("end_sec")
            out[-1]["title"] = f"{out[-1]['title']} + {item['title']}"
        else:
            out.append(item)

    for idx, segment in enumerate(out):
        segment["index"] = idx
    return out
