from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.message import TicketMessage
from app.models.ticket import Ticket


async def find_ticket_by_email_thread(
    db: AsyncSession,
    in_reply_to: str | None,
    references: list[str] | None,
) -> Ticket | None:
    message_ids = []
    if in_reply_to:
        message_ids.append(in_reply_to)
    if references:
        message_ids.extend(references)

    if not message_ids:
        return None

    result = await db.execute(
        select(TicketMessage)
        .where(TicketMessage.email_message_id.in_(message_ids))
        .order_by(TicketMessage.created_at.desc())
        .limit(1)
    )
    msg = result.scalar_one_or_none()
    if msg:
        ticket_result = await db.execute(select(Ticket).where(Ticket.id == msg.ticket_id))
        return ticket_result.scalar_one_or_none()

    ticket_result = await db.execute(
        select(Ticket).where(Ticket.email_message_id.in_(message_ids)).limit(1)
    )
    return ticket_result.scalar_one_or_none()
