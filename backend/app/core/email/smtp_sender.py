import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib

from app.models.email_account import EmailAccount

logger = logging.getLogger(__name__)


async def send_ticket_reply(
    email_account: EmailAccount,
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
    message_id: str | None = None,
    in_reply_to: str | None = None,
    references: str | None = None,
):
    if body_html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))
    else:
        msg = MIMEText(body_text, "plain", "utf-8")

    msg["From"] = email_account.email_address
    msg["To"] = to_email
    msg["Subject"] = subject

    if message_id:
        msg["Message-ID"] = message_id
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references

    try:
        await aiosmtplib.send(
            msg,
            hostname=email_account.smtp_host,
            port=email_account.smtp_port,
            username=email_account.username,
            password=email_account.password_encrypted,
            start_tls=True,
        )
        logger.info(f"Email sent to {to_email} for subject '{subject}'")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise
