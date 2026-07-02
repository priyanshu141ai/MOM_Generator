_models = {}


def transcribe_audio(path: str, model_size: str = "tiny") -> str:
    segments = transcribe_segments(path, model_size, vad_filter=True)
    if not segments:
        segments = transcribe_segments(path, model_size, vad_filter=False)
    return "\n".join(f"{s['start']:.1f}-{s['end']:.1f}: {s['text']}" for s in segments)


def transcribe_segments(path: str, model_size: str = "tiny", vad_filter: bool = True) -> list[dict]:
    from faster_whisper import WhisperModel

    if model_size not in _models:
        _models[model_size] = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = _models[model_size].transcribe(path, vad_filter=vad_filter)
    return [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]
