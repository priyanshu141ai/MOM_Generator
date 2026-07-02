# TODO

## High Priority

- Add Gmail app password in `.env` and test `/email/test`.
- Add Google OAuth credentials and test Calendar import.
- Add one-click **Diagnose Join** button in dashboard.
- Add visible recording progress/status polling in dashboard.
- Add delete/reset test meetings endpoint for cleanup.

## Accuracy

- Test `base`, `small`, and `medium` models on real meeting audio.
- Add language selector in dashboard.
- Add audio quality report: duration, RMS, max volume, silence percentage.
- Add optional manual transcript correction before MOM generation.

## Meeting Bot

- Auto-send chat consent message after joining.
- Detect host admission wait and show instruction in dashboard.
- Avoid duplicate Meet tabs for same meeting.
- Stop recording if meeting ends early.

## MOM Quality

- Improve action-item extraction.
- Add owner/due-date editor.
- Add export to PDF/DOCX.
- Add custom MOM template.

## Production

- Add auth/login.
- Move SQLite to Postgres.
- Move background work to Celery/RQ.
- Add structured logging.
- Add Dockerfile.
- Add CI after GitHub token has workflow permission.
