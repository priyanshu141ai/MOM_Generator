from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from app.config import settings
from app.db import get_session, init_db
from app.emailer import is_configured, send_mail
from app.models import Meeting, MeetingCreate, TranscriptIn
from app.mom import generate_mom
from app.bots.runner import run_meeting_bot
from app.bots.recorder import list_audio_devices
from app.scheduler import schedule_due_meetings
from app.transcriber import transcribe_audio

app = FastAPI(title="MOM Bot Backend")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/email/status")
def email_status():
    return {"configured": is_configured(), "mail_from": settings.mail_from or None}


@app.post("/email/test")
def email_test(to: str | None = None):
    target = to or settings.mail_test_to
    if not target:
        raise HTTPException(400, "Provide ?to=email or set MAIL_TEST_TO")
    sent = send_mail(target, "MOM Bot email test", "Email setup is working.")
    if not sent:
        raise HTTPException(400, "SMTP not configured")
    return {"ok": True, "sent_to": target}


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse("static/index.html")


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


@app.post("/meetings/{meeting_id}/send-mom")
def send_meeting_mom(meeting_id: int, session: Session = Depends(get_session)):
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    if not meeting.mom:
        raise HTTPException(400, "MOM not generated yet")
    sent = send_mail(meeting.recipient_email, f"MOM: {meeting.title}", meeting.mom)
    if not sent:
        raise HTTPException(400, "SMTP not configured")
    return {"ok": True, "sent_to": meeting.recipient_email}


@app.post("/meetings/{meeting_id}/record")
def record_meeting(meeting_id: int, background: BackgroundTasks, duration_sec: int = 60):
    background.add_task(run_meeting_bot, meeting_id, duration_sec)
    return {"ok": True, "meeting_id": meeting_id, "status": "recording_started"}


@app.post("/calendar/run-due")
def run_due_calendar(background: BackgroundTasks, window_min: int = 5, session: Session = Depends(get_session)):
    count = schedule_due_meetings(session, background, window_min)
    return {"ok": True, "queued": count}


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


@app.post("/meetings/{meeting_id}/upload-audio", response_model=Meeting)
async def upload_audio(
    meeting_id: int,
    file: UploadFile = File(...),
    model_size: str = "tiny",
    session: Session = Depends(get_session),
):
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")

    Path(settings.recordings_dir).mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    path = Path(settings.recordings_dir) / f"meeting_{meeting_id}_upload{suffix}"
    path.write_bytes(await file.read())

    meeting.recording_path = str(path)
    meeting.transcript = transcribe_audio(str(path), model_size)
    meeting.mom = generate_mom(meeting.title, meeting.transcript)
    meeting.status = "mom_ready"
    session.add(meeting)
    session.commit()
    session.refresh(meeting)
    return meeting
