from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> bool:
    settings = get_settings()
    if not settings.smtp_host:
        logger.info("SMTP not configured, skip email to %s: %s", to, subject)
        return False
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = settings.notify_from
        msg["To"] = to
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_tls:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error("Email failed: %s", e)
        return False


def notify_late_attendance(email: str, employee_name: str, late_minutes: int) -> bool:
    return send_email(
        email,
        "Late attendance alert",
        f"{employee_name} was late by {late_minutes} minutes today.",
    )


def notify_missing_checkout(email: str, employee_name: str, date_str: str) -> bool:
    return send_email(
        email,
        "Missing checkout alert",
        f"{employee_name} has no checkout recorded for {date_str}.",
    )


def notify_correction_status(email: str, status: str, date_str: str) -> bool:
    return send_email(
        email,
        f"Attendance correction {status}",
        f"Your attendance correction request for {date_str} is now: {status}.",
    )
