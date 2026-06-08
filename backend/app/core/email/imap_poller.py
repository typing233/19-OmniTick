import asyncio
import email
import logging
from email.header import decode_header
from email.utils import parseaddr

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.email_account import EmailAccount
from app.models.ticket import Ticket, TicketStatus
from app.models.message import TicketMessage, SenderType, MessageDirection
from app.models.audit import TicketAuditLog
from app.models.base import gen_id
from app.core.email.thread_tracker import find_ticket_by_email_thread

logger = logging.getLogger(__name__)


def decode_mime_header(value: str) -> str:
    if not value:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def extract_body(msg: email.message.Message) -> tuple[str, str | None]:
    text_body = ""
    html_body = None

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" and not text_body:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    text_body = payload.decode(charset, errors="replace")
            elif content_type == "text/html" and not html_body:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    html_body = payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            text_body = payload.decode(charset, errors="replace")

    return text_body, html_body


class ImapPoller:
    def __init__(self):
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("IMAP poller started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("IMAP poller stopped")

    async def _poll_loop(self):
        while self._running:
            try:
                await self._poll_all_accounts()
            except Exception as e:
                logger.error(f"IMAP poll error: {e}")
            await asyncio.sleep(60)

    async def _poll_all_accounts(self):
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(EmailAccount).where(EmailAccount.is_active == True)
            )
            accounts = result.scalars().all()

        for account in accounts:
            try:
                await self._poll_account(account)
            except Exception as e:
                logger.error(f"Error polling {account.email_address}: {e}")

    async def _poll_account(self, account: EmailAccount):
        import aioimaplib

        imap = aioimaplib.IMAP4_SSL(host=account.imap_host, port=account.imap_port)
        await imap.wait_hello_from_server()
        await imap.login(account.username, account.password_encrypted)
        await imap.select("INBOX")

        _, data = await imap.search("UNSEEN")
        if not data or not data[0]:
            await imap.logout()
            return

        message_nums = data[0].split()
        for num in message_nums:
            try:
                _, msg_data = await imap.fetch(num.decode(), "(RFC822)")
                if msg_data and len(msg_data) >= 2:
                    raw_email = msg_data[1]
                    if isinstance(raw_email, tuple) and len(raw_email) >= 2:
                        raw_email = raw_email[1]
                    if isinstance(raw_email, bytes):
                        await self._process_email(raw_email, account)
                await imap.store(num.decode(), "+FLAGS", "\\Seen")
            except Exception as e:
                logger.error(f"Error processing message {num}: {e}")

        await imap.logout()

        from app.models.base import utcnow
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(EmailAccount).where(EmailAccount.id == account.id))
            acct = result.scalar_one()
            acct.last_polled_at = utcnow()
            await db.commit()

    async def _process_email(self, raw_email: bytes, account: EmailAccount):
        msg = email.message_from_bytes(raw_email)

        message_id = msg.get("Message-ID", "")
        in_reply_to = msg.get("In-Reply-To", "")
        references_header = msg.get("References", "")
        references = references_header.split() if references_header else []
        from_addr = parseaddr(msg.get("From", ""))[1]
        subject = decode_mime_header(msg.get("Subject", "No Subject"))

        text_body, html_body = extract_body(msg)

        async with AsyncSessionLocal() as db:
            ticket = await find_ticket_by_email_thread(db, in_reply_to, references)

            if ticket:
                new_msg = TicketMessage(
                    id=gen_id(),
                    ticket_id=ticket.id,
                    sender_type=SenderType.CUSTOMER,
                    sender_email=from_addr,
                    body_text=text_body,
                    body_html=html_body,
                    email_message_id=message_id,
                    email_in_reply_to=in_reply_to,
                    direction=MessageDirection.INBOUND,
                )
                db.add(new_msg)

                if ticket.status == TicketStatus.PENDING_RESPONSE:
                    from app.core.state_machine import do_transition
                    try:
                        audit = do_transition(ticket, TicketStatus.IN_PROGRESS, None)
                        db.add(audit)
                    except ValueError:
                        pass
            else:
                ticket = Ticket(
                    id=gen_id(),
                    subject=subject,
                    status=TicketStatus.NEW,
                    requester_email=from_addr,
                    email_message_id=message_id,
                    email_account_id=account.id,
                )
                db.add(ticket)

                first_msg = TicketMessage(
                    id=gen_id(),
                    ticket_id=ticket.id,
                    sender_type=SenderType.CUSTOMER,
                    sender_email=from_addr,
                    body_text=text_body,
                    body_html=html_body,
                    email_message_id=message_id,
                    direction=MessageDirection.INBOUND,
                )
                db.add(first_msg)

                db.add(TicketAuditLog(
                    id=gen_id(),
                    ticket_id=ticket.id,
                    actor_id=None,
                    action="created_from_email",
                ))

            await db.commit()
