import base64
import os
from pathlib import Path
from types import SimpleNamespace

from audio_engine.youtube import _auth_args, download_audio


def test_download_audio_retries_when_selected_format_is_unavailable(tmp_path):
    calls: list[list[str]] = []

    def fake_run(args, capture_output, text, check):
        del capture_output, text, check
        calls.append(args)
        chosen_format = args[args.index("-f") + 1]
        if chosen_format == "251":
            return SimpleNamespace(
                returncode=1,
                stdout="",
                stderr="ERROR: [youtube] abc123: Requested format is not available",
            )

        output_path = Path(args[args.index("-o") + 1].replace("%(ext)s", "mp3"))
        output_path.write_text("fake-audio")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    metadata = {
        "formats": [
            {"format_id": "251", "acodec": "opus", "vcodec": "none", "abr": 160, "url": "https://example.com"},
        ]
    }

    import audio_engine.youtube as youtube

    original_run = youtube.subprocess.run
    youtube.subprocess.run = fake_run
    try:
        output = download_audio(
            "https://www.youtube.com/watch?v=abc123",
            tmp_path,
            file_stem="job-1",
            metadata=metadata,
        )
    finally:
        youtube.subprocess.run = original_run

    assert output.name == "job-1.mp3"
    assert [call[call.index("-f") + 1] for call in calls] == ["251", "bestaudio/best"]


def test_auth_args_uses_runtime_base64_cookie_secret(tmp_path):
    import audio_engine.youtube as youtube

    cookie_path = tmp_path / "yt_cookies.txt"
    cookie_body = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tSID\tvalue\n"
    original_cookies_file = youtube._COOKIES_FILE
    original_env = os.environ.copy()
    youtube._COOKIES_FILE = cookie_path
    os.environ.pop("YT_COOKIES_PATH", None)
    os.environ["YT_COOKIES_B64"] = base64.b64encode(cookie_body.encode()).decode()
    try:
        args = _auth_args()
    finally:
        youtube._COOKIES_FILE = original_cookies_file
        os.environ.clear()
        os.environ.update(original_env)

    assert args == ["--cookies", str(cookie_path)]
    assert cookie_path.read_text() == cookie_body
