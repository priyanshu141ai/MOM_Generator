from email.message import EmailMessage
import smtplib

from app.config import settings


def send_mail(to: str, subject: str, body: str):
    if not is_configured():
        return False

    msg = EmailMessage()
    msg["From"] = settings.mail_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    msg.add_alternative(markdown_to_html(body), subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
    return True


def is_configured() -> bool:
    if not settings.smtp_host or not settings.mail_from:
        return False
    return not settings.smtp_user or bool(settings.smtp_password)


def markdown_to_html(text: str) -> str:
    html = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = html.replace("\n", "<br>")
    return f"<div style='font-family:Arial,sans-serif;line-height:1.5;color:#111'>{html}</div>"
