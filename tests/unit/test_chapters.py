from audio_engine.chapters import chapters_to_segments, extract_chapters_from_description


def test_extract_chapters_handles_multiple_formats():
    text = """00:00 - 03:00 - Intro
03:00 Song A
12:10 Song B
"""
    chapters = extract_chapters_from_description(text)
    assert chapters == [("00:00", "Intro"), ("03:00", "Song A"), ("12:10", "Song B")]


def test_chapters_to_segments_resolves_end_times():
    segments = chapters_to_segments([("00:00", "A"), ("03:00", "B")], duration_sec=600)
    assert segments[0]["end_sec"] == 180
    assert segments[1]["end_sec"] == 600
