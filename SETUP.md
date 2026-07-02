# MOM Bot Setup

## Run Backend

```powershell
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Dashboard:

```text
http://127.0.0.1:8001/
```

API docs:

```text
http://127.0.0.1:8001/docs
```

## Required `.env`

```env
FFMPEG_AUDIO_INPUT=audio="CABLE Output (VB-Audio Virtual Cable)"
BOT_HEADLESS=false
BOT_BROWSER_PROFILE="C:/Users/kinsh.000/AppData/Local/Google/Chrome/User Data"
BOT_BROWSER_CHANNEL="chrome"
BOT_CHROME_PROFILE_DIRECTORY="Profile 2"
BOT_CDP_URL="http://127.0.0.1:9222"
DEFAULT_TRANSCRIBE_MODEL="small"
DEFAULT_TRANSCRIBE_LANGUAGE="en"
```

## Start Chrome Debug

Close normal Chrome first, then:

```powershell
.\scripts\start_chrome_debug.ps1 "Profile 2"
```

Check:

```text
http://127.0.0.1:8001/bot/browser-status
```

## Meeting Flow

1. Create meeting in dashboard.
2. Click **Record**.
3. If Meet asks host approval, admit `botkumar901@gmail.com`.
4. Speak during recording.
5. Click **Transcribe**.
6. Check **Transcript** and **MOM** tabs.

## Better Transcription

Default uses `small`. For faster/lower accuracy:

```text
POST /meetings/{id}/transcribe?model_size=base&language=en
```

## Email

Use Gmail App Password, not normal password:

```env
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="botkumar901@gmail.com"
SMTP_PASSWORD="app-password"
MAIL_FROM="botkumar901@gmail.com"
```

Test:

```text
POST /email/test?to=your@email.com
```
