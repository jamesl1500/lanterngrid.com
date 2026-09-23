from app.core.config import get_settings
from app.core.email import Email


def verification_email(to: str, display_name: str, token: str) -> Email:
    link = f"{get_settings().web_url}/verify-email?token={token}"
    return Email(
        to=to,
        subject="Verify your email for Lantern Grid",
        text=(
            f"Hi {display_name},\n\n"
            f"Confirm this is your email address by opening the link below:\n\n{link}\n\n"
            "The link works for 24 hours. If you didn't sign up for Lantern Grid, ignore this.\n"
        ),
    )


def password_reset_email(to: str, display_name: str, token: str) -> Email:
    link = f"{get_settings().web_url}/reset-password?token={token}"
    return Email(
        to=to,
        subject="Reset your Lantern Grid password",
        text=(
            f"Hi {display_name},\n\n"
            f"Choose a new password here:\n\n{link}\n\n"
            "The link works for 1 hour. If you didn't ask for this, ignore this email and "
            "your password stays the same.\n"
        ),
    )
