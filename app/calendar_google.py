import re
import secrets
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlmodel import Session, select

from app.config import settings
from app.models import Meeting, Platform

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def google_configured() -> bool:
    return bool(settings.google_client_id and settings.google_client_secret)


def auth_url() -> str:
    flow = Flow.from_client_config(client_config(), scopes=SCOPES, redirect_uri=settings.google_redirect_uri)
    state = secrets.token_urlsafe(32)
    Path(settings.google_oauth_state_file).write_text(state)
    url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return url


def save_callback_token(code: str, state: str):
    expected = Path(settings.google_oauth_state_file)
    if not expected.exists() or expected.read_text().strip() != state:
        raise RuntimeError("Invalid Google OAuth state")
    flow = Flow.from_client_config(client_config(), scopes=SCOPES, redirect_uri=settings.google_redirect_uri)
    flow.fetch_token(code=code)
    Path(settings.google_token_file).write_text(flow.credentials.to_json())
    expected.unlink(missing_ok=True)


def import_google_meetings(session: Session, days: int = 7) -> int:
    if not Path(settings.google_token_file).exists():
        raise RuntimeError("Google Calendar is not connected")
    creds = Credentials.from_authorized_user_file(settings.google_token_file, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        Path(settings.google_token_file).write_text(creds.to_json())
    service = build("calendar", "v3", credentials=creds)
    now = datetime.utcnow()
    events = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat() + "Z",
        timeMax=(now + timedelta(days=days)).isoformat() + "Z",
        singleEvents=True,
        orderBy="startTime",
    ).execute().get("items", [])

    created = 0
    for event in events:
        link = extract_meet_link(event)
        if not link or exists(session, link):
            continue
        meeting = Meeting(
            title=event.get("summary") or "Calendar meeting",
            platform=Platform.google_meet,
            meeting_url=link,
            recipient_email=attendee_email(event),
            starts_at=parse_start(event),
        )
        session.add(meeting)
        created += 1
    session.commit()
    return created


def client_config() -> dict:
    if not google_configured():
        raise RuntimeError("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }


def extract_meet_link(event: dict) -> str:
    blob = " ".join(str(event.get(k, "")) for k in ["hangoutLink", "location", "description"])
    m = re.search(r"https://meet\.google\.com/[a-z-]+", blob)
    return m.group(0) if m else ""


def parse_start(event: dict):
    value = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def attendee_email(event: dict) -> str:
    attendees = event.get("attendees") or []
    if attendees:
        return attendees[0].get("email", "")
    return event.get("organizer", {}).get("email") or event.get("creator", {}).get("email") or settings.mail_from


def exists(session: Session, meeting_url: str) -> bool:
    return bool(session.exec(select(Meeting).where(Meeting.meeting_url == meeting_url)).first())
