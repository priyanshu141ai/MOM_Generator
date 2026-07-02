import subprocess
from pathlib import Path

import imageio_ffmpeg

from app.config import settings

_models = {}


def transcribe_audio(path: str, model_size: str | None = None, language: str | None = None) -> str:
    model_size = model_size or settings.default_transcribe_model
    language = language or settings.default_transcribe_language or None
    clean_path = preprocess_audio(path)
    segments = transcribe_segments(clean_path, model_size, language=language, vad_filter=True)
    if not segments:
        segments = transcribe_segments(clean_path, model_size, language=language, vad_filter=False)
    return "\n".join(f"{s['start']:.1f}-{s['end']:.1f}: {s['text']}" for s in segments)


def transcribe_segments(path: str, model_size: str = "small", language: str | None = "en", vad_filter: bool = True) -> list[dict]:
    from faster_whisper import WhisperModel

    if model_size not in _models:
        _models[model_size] = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = _models[model_size].transcribe(
        path,
        language=language,
        beam_size=5,
        best_of=5,
        temperature=0,
        condition_on_previous_text=False,
        vad_filter=vad_filter,
        vad_parameters={"min_silence_duration_ms": 700},
    )
    return [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]


def preprocess_audio(path: str) -> str:
    src = Path(path)
    out = src.with_name(f"{src.stem}_clean.wav")
    cmd = [
        imageio_ffmpeg.get_ffmpeg_exe(),
        "-y",
        "-i",
        str(src),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-af",
        "highpass=f=80,lowpass=f=7800,loudnorm=I=-16:TP=-1.5:LRA=11",
        str(out),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return str(out)
