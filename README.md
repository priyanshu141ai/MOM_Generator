# MOM Bot Backend

Free/local-first FastAPI backend for meeting MOM generation.

## Run

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Open: http://127.0.0.1:8000/docs

## MVP

- Add Google Meet / Zoom / Teams meeting link
- Store meeting
- Upload transcript text for now
- Generate MOM/action items
- Email MOM if SMTP is configured

Actual auto-join/audio recording needs browser worker next.

## Google Meet recording worker

Install browser once:

```bash
playwright install chromium
```

Set `.env`:

```env
FFMPEG_AUDIO_INPUT=audio="Stereo Mix (Realtek(R) Audio)"
BOT_HEADLESS=false
```

Then call:

```http
POST /meetings/{id}/record?duration_sec=60
```

Note: Windows audio device name must match FFmpeg dshow device.

## Email setup

For Gmail, create an App Password, then set:

```env
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="your@gmail.com"
SMTP_PASSWORD="your-16-character-app-password"
MAIL_FROM="your@gmail.com"
MAIL_TEST_TO="your@gmail.com"
```

Test:

```http
POST /email/test?to=your@gmail.com
```

## Login bot Google account

Do not save Google password in code. Run:

```bash
python scripts/login_google.py
```

Login manually in opened browser. Close it after login. The bot reuses `./browser-profile`.
