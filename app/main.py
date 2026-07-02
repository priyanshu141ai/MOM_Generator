from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from sqlmodel import Session, select

from app.db import get_session, init_db
from app.emailer import send_mail
from app.models import Meeting, MeetingCreate, TranscriptIn
from app.mom import generate_mom
from app.bots.runner import run_meeting_bot
from app.bots.recorder import list_audio_devices
from app.transcriber import transcribe_audio

app = FastAPI(title="MOM Bot Backend")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/meetings", response_model=Meeting)
def create_meeting(data: MeetingCreate, session: Session = Depends(get_session)):
    meeting = Meeting.model_validate(data)
    session.add(meeting)
    session.commit()
    session.refresh(meeting)
    return meeting


@app.get("/meetings", response_model=list[Meeting])
def list_meetings(session: Session = Depends(get_session)):
    return session.exec(select(Meeting).order_by(Meeting.created_at.desc())).all()


@app.get("/meetings/{meeting_id}", response_model=Meeting)
def get_meeting(meeting_id: int, session: Session = Depends(get_session)):
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    return meeting


@app.post("/meetings/{meeting_id}/transcript", response_model=Meeting)
def add_transcript(meeting_id: int, data: TranscriptIn, session: Session = Depends(get_session)):
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")

    meeting.transcript = data.transcript
    meeting.mom = generate_mom(meeting.title, data.transcript)
    meeting.status = "mom_ready"
    session.add(meeting)
    session.commit()
    session.refresh(meeting)

    if data.send_email:
        send_mail(meeting.recipient_email, f"MOM: {meeting.title}", meeting.mom)
    return meeting


@app.post("/meetings/{meeting_id}/record")
def record_meeting(meeting_id: int, background: BackgroundTasks, duration_sec: int = 60):
    background.add_task(run_meeting_bot, meeting_id, duration_sec)
    return {"ok": True, "meeting_id": meeting_id, "status": "recording_started"}


@app.get("/audio-devices")
def audio_devices():
    return {"ffmpeg_output": list_audio_devices()}


@app.post("/meetings/{meeting_id}/transcribe", response_model=Meeting)
def transcribe_meeting(meeting_id: int, model_size: str = "tiny", session: Session = Depends(get_session)):
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    if not meeting.recording_path:
        raise HTTPException(400, "No recording found")

    meeting.transcript = transcribe_audio(meeting.recording_path, model_size)
    meeting.mom = generate_mom(meeting.title, meeting.transcript)
    meeting.status = "mom_ready"
    session.add(meeting)
    session.commit()
    session.refresh(meeting)
    return meeting
