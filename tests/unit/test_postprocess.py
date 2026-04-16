from audio_engine.postprocess import enforce_min_lengths


def test_merge_short_tail_segment():
    segments = [
        {"index": 0, "start_sec": 0, "end_sec": 120, "title": "A", "strategy": "chapter"},
        {"index": 1, "start_sec": 120, "end_sec": 130, "title": "B", "strategy": "chapter"},
    ]
    out = enforce_min_lengths(segments, min_length_sec=60, merge_threshold_sec=30, duration_sec=300)
    assert len(out) == 1
    assert out[0]["end_sec"] == 130
