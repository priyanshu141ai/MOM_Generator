from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class Platform(str, Enum):
    google_meet = "google_meet"
    zoom = "zoom"
    teams = "teams"


class Meeting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    platform: Platform
    meeting_url: str
    recipient_email: str
    starts_at: Optional[datetime] = None
    status: str = "created"
    transcript: str = ""
    mom: str = ""
    recording_path: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MeetingCreate(SQLModel):
    title: str
    platform: Platform
    meeting_url: str
    recipient_email: str
    starts_at: Optional[datetime] = None


class TranscriptIn(SQLModel):
    transcript: str
    send_email: bool = False
