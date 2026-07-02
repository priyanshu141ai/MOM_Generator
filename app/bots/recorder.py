import subprocess
from pathlib import Path

import imageio_ffmpeg

from app.config import settings


def ffmpeg_bin() -> str:
    return settings.ffmpeg_bin if settings.ffmpeg_bin != "ffmpeg" else imageio_ffmpeg.get_ffmpeg_exe()


def list_audio_devices() -> str:
    proc = subprocess.run(
        [ffmpeg_bin(), "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
        capture_output=True,
        text=True,
    )
    return proc.stderr


def start_audio_recording(meeting_id: int) -> tuple[subprocess.Popen, str]:
    Path(settings.recordings_dir).mkdir(parents=True, exist_ok=True)
    out = str(Path(settings.recordings_dir) / f"meeting_{meeting_id}.wav")

    if not settings.ffmpeg_audio_input:
        raise RuntimeError("Set FFMPEG_AUDIO_INPUT in .env")

    audio_input = settings.ffmpeg_audio_input.replace('audio="', "audio=").rstrip('"')
    cmd = [
        ffmpeg_bin(),
        "-y",
        "-f",
        "dshow",
        "-i",
        audio_input,
        "-ac",
        "1",
        "-ar",
        "16000",
        out,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc, out


def stop_audio_recording(proc: subprocess.Popen):
    if proc.stdin:
        proc.stdin.write(b"q")
        proc.stdin.flush()
    proc.wait(timeout=10)
