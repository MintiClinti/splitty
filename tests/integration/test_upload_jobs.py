from fastapi.testclient import TestClient

from app.main import app


def test_create_upload_job_accepts_audio_file(monkeypatch, tmp_path):
    client = TestClient(app)
    recorded = {}

    monkeypatch.setattr("app.api.routes.repository.create_job", lambda _: {"id": "job-123", "status": "pending"})

    async def fake_save_upload(job_id, upload):
        recorded["saved_job_id"] = job_id
        return tmp_path / "job-123.mp3"

    monkeypatch.setattr("app.api.routes._save_upload", fake_save_upload)
    monkeypatch.setattr(
        "app.api.routes.job_runner.submit",
        lambda fn, *args, **kwargs: recorded.update({"fn": fn.__name__, "args": args, "kwargs": kwargs}),
    )

    response = client.post(
        "/api/v1/jobs",
        files={"file": ("demo.mp3", b"fake-audio", "audio/mpeg")},
        data={"title": "Demo Upload"},
    )

    assert response.status_code == 200
    assert response.json() == {"jobId": "job-123", "status": "pending"}
    assert recorded["saved_job_id"] == "job-123"
    assert recorded["fn"] == "run_uploaded_analysis"
    assert recorded["args"] == ("job-123", str(tmp_path / "job-123.mp3"), "Demo Upload")


def test_create_upload_job_accepts_chapter_sidecar(monkeypatch, tmp_path):
    client = TestClient(app)
    recorded = {}

    monkeypatch.setattr("app.api.routes.repository.create_job", lambda _: {"id": "job-456", "status": "pending"})

    async def fake_save_upload(job_id, upload):
        return tmp_path / "job-456.mp3"

    monkeypatch.setattr("app.api.routes._save_upload", fake_save_upload)
    monkeypatch.setattr(
        "app.api.routes.job_runner.submit",
        lambda fn, *args, **kwargs: recorded.update({"fn": fn.__name__, "args": args}),
    )

    response = client.post(
        "/api/v1/jobs",
        files={
            "file": ("demo.mp3", b"fake-audio", "audio/mpeg"),
            "chapters_file": ("demo.chapters.txt", b"00:00 Intro\n03:00 Song A\n", "text/plain"),
        },
        data={"title": "Demo Upload"},
    )

    assert response.status_code == 200
    assert recorded["fn"] == "run_uploaded_analysis"
    assert recorded["args"] == (
        "job-456",
        str(tmp_path / "job-456.mp3"),
        "Demo Upload",
        "00:00 Intro\n03:00 Song A",
    )
