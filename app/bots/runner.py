import asyncio

from sqlmodel import Session

from app.bots.google_meet import join_google_meet
from app.bots.recorder import start_audio_recording, stop_audio_recording
from app.db import engine
from app.models import Meeting, Platform


def run_meeting_bot(meeting_id: int, duration_sec: int = 60):
    with Session(engine) as session:
        meeting = session.get(Meeting, meeting_id)
        if not meeting:
            raise RuntimeError("Meeting not found")
        if meeting.platform != Platform.google_meet:
            raise RuntimeError("Only Google Meet worker is implemented")

        try:
            meeting.status = "recording"
            session.add(meeting)
            session.commit()

            proc, path = start_audio_recording(meeting.id)
            try:
                asyncio.run(join_google_meet(meeting.meeting_url, duration_sec))
            finally:
                stop_audio_recording(proc)

            meeting.recording_path = path
            meeting.status = "recorded"
        except Exception as exc:
            meeting.status = f"recording_failed: {exc}"
        finally:
            session.add(meeting)
            session.commit()
