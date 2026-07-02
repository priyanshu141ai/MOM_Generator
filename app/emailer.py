from email.message import EmailMessage
import smtplib

from app.config import settings


def send_mail(to: str, subject: str, body: str):
    if not settings.smtp_host or not settings.mail_from:
        return False

    msg = EmailMessage()
    msg["From"] = settings.mail_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
    return True
