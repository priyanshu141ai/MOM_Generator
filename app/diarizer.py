from app.config import settings
from app.transcriber import transcribe_segments

_pipeline = None


def diarize_transcript(path: str, model_size: str = "tiny") -> str:
    global _pipeline
    if not settings.hf_token:
        raise RuntimeError("Set HF_TOKEN in .env for speaker diarization")

    from pyannote.audio import Pipeline

    if _pipeline is None:
        _pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=settings.hf_token,
        )

    diarization = _pipeline(path)
    speakers = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        speakers.append({"start": turn.start, "end": turn.end, "speaker": speaker})

    lines = []
    for seg in transcribe_segments(path, model_size):
        label = speaker_for(seg["start"], seg["end"], speakers)
        lines.append(f"{seg['start']:.1f}-{seg['end']:.1f}: {label}: {seg['text']}")
    return "\n".join(lines)


def speaker_for(start: float, end: float, speakers: list[dict]) -> str:
    best = ("Speaker ?", 0.0)
    for item in speakers:
        overlap = max(0.0, min(end, item["end"]) - max(start, item["start"]))
        if overlap > best[1]:
            best = (item["speaker"].replace("SPEAKER_", "Speaker "), overlap)
    return best[0]
