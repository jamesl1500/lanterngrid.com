import asyncio
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

import structlog

from app.core.config import Settings, get_settings

log = structlog.get_logger()


@dataclass(frozen=True)
class Email:
    to: str
    subject: str
    text: str


# Mail "sent" with the memory backend lands here, for tests to read.
outbox: list[Email] = []


def _send_smtp(email: Email, settings: Settings) -> None:
    message = EmailMessage()
    message["From"] = settings.email_from
    message["To"] = email.to
    message["Subject"] = email.subject
    message.set_content(email.text)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_username and settings.smtp_password:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


async def send_email(email: Email) -> None:
    settings = get_settings()
    match settings.email_backend:
        case "memory":
            outbox.append(email)
        case "console":
            log.info("email", to=email.to, subject=email.subject, text=email.text)
        case "smtp":
            try:
                await asyncio.to_thread(_send_smtp, email, settings)
            except (OSError, smtplib.SMTPException):
                log.exception("email_send_failed", to=email.to, subject=email.subject)
