from datetime import datetime, timedelta

from fastapi import BackgroundTasks
from sqlmodel import Session, select

from app.bots.runner import run_meeting_bot
from app.models import Meeting


def schedule_due_meetings(session: Session, background: BackgroundTasks, window_min: int = 5) -> int:
    now = datetime.utcnow()
    since = now - timedelta(minutes=1)
    until = now + timedelta(minutes=window_min)
    rows = session.exec(
        select(Meeting).where(
            Meeting.starts_at != None,
            Meeting.starts_at >= since,
            Meeting.starts_at <= until,
            Meeting.status == "created",
        )
    ).all()
    for meeting in rows:
        meeting.status = "queued"
        session.add(meeting)
        background.add_task(run_meeting_bot, meeting.id, 3600)
    session.commit()
    return len(rows)
