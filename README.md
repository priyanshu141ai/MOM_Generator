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

## Speaker diarization

Create a Hugging Face token and accept access for `pyannote/speaker-diarization-3.1`, then set:

```env
HF_TOKEN="hf_xxx"
```

Run:

```http
POST /meetings/{id}/diarize?model_size=tiny
```

## Login bot Google account

Do not save Google password in code. Run:

```bash
python scripts/login_google.py
```

Login manually in opened browser. Close it after login. The bot reuses `./browser-profile`.

## Reliable Google Meet mode

Start normal Chrome with remote debugging and the profile where the bot Google account is signed in:

```powershell
.\scripts\start_chrome_debug.ps1 "Profile 2"
```

Check:

```http
GET /bot/browser-status
```

Expected:

```json
{"configured": true, "ok": true}
```

If Meet blocks join, inspect:

```text
bot-debug/last_meet.png
```

Join diagnostics:

```http
POST /meetings/{id}/diagnose-join
```

If status says the bot is waiting for host admission, open the meeting as host and click **Admit** for `botkumar901@gmail.com`, or add that account to the Calendar invite before the meeting.

## Google Calendar sync

Create a Google OAuth client and add this redirect URI:

```text
http://127.0.0.1:8001/calendar/google/callback
```

Set:

```env
GOOGLE_CLIENT_ID="..."
GOOGLE_CLIENT_SECRET="..."
GOOGLE_REDIRECT_URI="http://127.0.0.1:8001/calendar/google/callback"
```

Flow:

```http
GET /calendar/google/auth-url
GET /calendar/google/status
POST /calendar/google/import?days=7
POST /calendar/run-due?window_min=5
```
