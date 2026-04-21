import shutil


def check_dependencies() -> dict[str, bool]:
    required_bins = ["ffmpeg", "ffprobe"]
    return {name: shutil.which(name) is not None for name in required_bins}
