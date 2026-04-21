from app.services.analysis_service import _build_upload_metadata


def test_build_upload_metadata_uses_file_metadata(monkeypatch, tmp_path):
    source_path = tmp_path / "demo-track.m4a"
    source_path.write_text("placeholder")
    monkeypatch.setattr("app.services.analysis_service.probe_duration", lambda _: 123.9)

    metadata = _build_upload_metadata(source_path, "  Demo Title  ", "00:00 Intro")

    assert metadata["title"] == "Demo Title"
    assert metadata["duration"] == 123
    assert metadata["description"] == "00:00 Intro"
    assert metadata["source"] == "upload"
    assert metadata["original_filename"] == "demo-track.m4a"
