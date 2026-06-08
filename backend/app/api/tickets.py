from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.ticket import Ticket, TicketStatus, ticket_labels
from app.models.label import Label
from app.models.message import TicketMessage, SenderType, MessageDirection
from app.models.audit import TicketAuditLog
from app.models.base import gen_id
from app.core.state_machine import do_transition, get_allowed_transitions
from app.schemas.ticket import (
    TicketCreate, TicketUpdate, TicketOut, TicketListResponse,
    TicketTransition, TicketAssign, TicketLabelAttach,
)
from app.schemas.message import MessageOut, MessageCreate, AuditLogOut

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[TicketStatus] = Query(None, alias="status"),
    assignee_id: Optional[str] = Query(None),
    label_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(Ticket).options(selectinload(Ticket.labels), selectinload(Ticket.assignee))
    count_query = select(func.count(Ticket.id))

    if status_filter:
        query = query.where(Ticket.status == status_filter)
        count_query = count_query.where(Ticket.status == status_filter)
    if assignee_id:
        query = query.where(Ticket.assignee_id == assignee_id)
        count_query = count_query.where(Ticket.assignee_id == assignee_id)
    if label_id:
        query = query.join(ticket_labels).where(ticket_labels.c.label_id == label_id)
        count_query = count_query.join(ticket_labels).where(ticket_labels.c.label_id == label_id)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Ticket.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tickets = result.scalars().unique().all()

    return TicketListResponse(items=tickets, total=total, page=page, page_size=page_size)


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    body: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = Ticket(
        id=gen_id(),
        subject=body.subject,
        priority=body.priority,
        assignee_id=body.assignee_id,
        requester_email=body.requester_email,
    )

    if body.label_ids:
        result = await db.execute(select(Label).where(Label.id.in_(body.label_ids)))
        ticket.labels = list(result.scalars().all())

    db.add(ticket)

    audit = TicketAuditLog(
        id=gen_id(),
        ticket_id=ticket.id,
        actor_id=current_user.id,
        action="created",
    )
    db.add(audit)

    if body.body:
        msg = TicketMessage(
            id=gen_id(),
            ticket_id=ticket.id,
            sender_type=SenderType.CUSTOMER,
            sender_email=body.requester_email,
            body_text=body.body,
            direction=MessageDirection.INBOUND,
        )
        db.add(msg)

    await db.commit()
    await db.refresh(ticket, ["labels", "assignee"])
    return ticket


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Ticket)
        .options(selectinload(Ticket.labels), selectinload(Ticket.assignee))
        .where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(
    ticket_id: str,
    body: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Ticket).options(selectinload(Ticket.labels), selectinload(Ticket.assignee))
        .where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if body.subject is not None and body.subject != ticket.subject:
        db.add(TicketAuditLog(
            id=gen_id(), ticket_id=ticket.id, actor_id=current_user.id,
            action="field_change", field_name="subject",
            old_value=ticket.subject, new_value=body.subject,
        ))
        ticket.subject = body.subject
    if body.priority is not None and body.priority != ticket.priority:
        db.add(TicketAuditLog(
            id=gen_id(), ticket_id=ticket.id, actor_id=current_user.id,
            action="field_change", field_name="priority",
            old_value=ticket.priority.value, new_value=body.priority.value,
        ))
        ticket.priority = body.priority
    if body.requester_email is not None and body.requester_email != ticket.requester_email:
        db.add(TicketAuditLog(
            id=gen_id(), ticket_id=ticket.id, actor_id=current_user.id,
            action="field_change", field_name="requester_email",
            old_value=ticket.requester_email, new_value=body.requester_email,
        ))
        ticket.requester_email = body.requester_email
    if body.email_account_id is not None and body.email_account_id != ticket.email_account_id:
        ticket.email_account_id = body.email_account_id

    await db.commit()
    await db.refresh(ticket, ["labels", "assignee"])
    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Ticket)
        .options(
            selectinload(Ticket.messages),
            selectinload(Ticket.audit_logs),
            selectinload(Ticket.labels),
        )
        .where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.labels.clear()
    await db.delete(ticket)
    await db.commit()


@router.post("/{ticket_id}/transition", response_model=TicketOut)
async def transition_ticket(
    ticket_id: str,
    body: TicketTransition,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Ticket).options(selectinload(Ticket.labels), selectinload(Ticket.assignee))
        .where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    try:
        audit = do_transition(ticket, body.status, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.add(audit)
    await db.commit()
    await db.refresh(ticket, ["labels", "assignee"])
    return ticket


@router.post("/{ticket_id}/assign", response_model=TicketOut)
async def assign_ticket(
    ticket_id: str,
    body: TicketAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Ticket).options(selectinload(Ticket.labels), selectinload(Ticket.assignee))
        .where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    old_assignee = ticket.assignee_id
    ticket.assignee_id = body.assignee_id
    db.add(TicketAuditLog(
        id=gen_id(), ticket_id=ticket.id, actor_id=current_user.id,
        action="assign", field_name="assignee_id",
        old_value=old_assignee, new_value=body.assignee_id,
    ))
    await db.commit()
    await db.refresh(ticket, ["labels", "assignee"])
    return ticket


@router.post("/{ticket_id}/labels", response_model=TicketOut)
async def attach_labels(
    ticket_id: str,
    body: TicketLabelAttach,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Ticket).options(selectinload(Ticket.labels), selectinload(Ticket.assignee))
        .where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    labels_result = await db.execute(select(Label).where(Label.id.in_(body.label_ids)))
    new_labels = list(labels_result.scalars().all())
    for label in new_labels:
        if label not in ticket.labels:
            ticket.labels.append(label)
            db.add(TicketAuditLog(
                id=gen_id(), ticket_id=ticket.id, actor_id=current_user.id,
                action="label_add", field_name="labels",
                new_value=label.name,
            ))

    await db.commit()
    await db.refresh(ticket, ["labels", "assignee"])
    return ticket


@router.delete("/{ticket_id}/labels/{label_id}", response_model=TicketOut)
async def detach_label(
    ticket_id: str,
    label_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Ticket).options(selectinload(Ticket.labels), selectinload(Ticket.assignee))
        .where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    label_to_remove = None
    for label in ticket.labels:
        if label.id == label_id:
            label_to_remove = label
            break

    if label_to_remove:
        ticket.labels.remove(label_to_remove)
        db.add(TicketAuditLog(
            id=gen_id(), ticket_id=ticket.id, actor_id=current_user.id,
            action="label_remove", field_name="labels",
            old_value=label_to_remove.name,
        ))
        await db.commit()
        await db.refresh(ticket, ["labels", "assignee"])

    return ticket


@router.get("/{ticket_id}/messages", response_model=list[MessageOut])
async def list_messages(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TicketMessage)
        .where(TicketMessage.ticket_id == ticket_id)
        .order_by(TicketMessage.created_at)
    )
    return result.scalars().all()


@router.post("/{ticket_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def create_message(
    ticket_id: str,
    body: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    msg = TicketMessage(
        id=gen_id(),
        ticket_id=ticket_id,
        sender_type=SenderType.AGENT,
        sender_id=current_user.id,
        sender_email=current_user.email,
        body_text=body.body_text,
        body_html=body.body_html,
        direction=body.direction,
    )
    db.add(msg)

    db.add(TicketAuditLog(
        id=gen_id(), ticket_id=ticket_id, actor_id=current_user.id,
        action="reply",
    ))

    if body.direction == MessageDirection.OUTBOUND and ticket.email_account_id and ticket.requester_email:
        from app.core.email.smtp_sender import send_ticket_reply
        msg.email_message_id = f"<ticket-{ticket_id}-msg-{msg.id}@omnitick>"
        last_msg = await db.execute(
            select(TicketMessage)
            .where(TicketMessage.ticket_id == ticket_id, TicketMessage.email_message_id.isnot(None))
            .order_by(TicketMessage.created_at.desc())
            .limit(1)
        )
        last = last_msg.scalar_one_or_none()
        if last:
            msg.email_in_reply_to = last.email_message_id

        from app.models.email_account import EmailAccount
        acct_result = await db.execute(
            select(EmailAccount).where(EmailAccount.id == ticket.email_account_id)
        )
        email_account = acct_result.scalar_one_or_none()
        if email_account:
            await send_ticket_reply(
                email_account=email_account,
                to_email=ticket.requester_email,
                subject=f"Re: {ticket.subject}",
                body_text=body.body_text,
                body_html=body.body_html,
                message_id=msg.email_message_id,
                in_reply_to=msg.email_in_reply_to,
                references=ticket.email_message_id,
            )

    await db.commit()
    await db.refresh(msg)
    return msg


@router.get("/{ticket_id}/audit-log", response_model=list[AuditLogOut])
async def get_audit_log(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TicketAuditLog)
        .where(TicketAuditLog.ticket_id == ticket_id)
        .order_by(TicketAuditLog.created_at)
    )
    return result.scalars().all()
