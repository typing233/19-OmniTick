from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_customer, get_portal_tenant_id, optional_security
from app.models.customer import Customer
from app.models.ticket import Ticket, TicketStatus, TicketPriority
from app.models.message import TicketMessage, SenderType, MessageDirection
from app.models.audit import TicketAuditLog
from app.models.base import gen_id
from app.schemas.portal import (
    PortalTicketCreate, PortalTicketOut, PortalTicketDetailOut,
    PortalTicketListResponse, PortalMessageCreate, PortalMessageOut,
    PortalGuestTicketCreate,
)

DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"

router = APIRouter(prefix="/portal/tickets", tags=["portal-tickets"])


@router.get("", response_model=PortalTicketListResponse)
async def list_my_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
    tenant_id: str = Depends(get_portal_tenant_id),
):
    query = select(Ticket).where(
        Ticket.tenant_id == tenant_id, Ticket.customer_id == customer.id
    )
    count_query = select(func.count(Ticket.id)).where(
        Ticket.tenant_id == tenant_id, Ticket.customer_id == customer.id
    )

    if status_filter:
        query = query.where(Ticket.status == TicketStatus(status_filter))
        count_query = count_query.where(Ticket.status == TicketStatus(status_filter))

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Ticket.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tickets = result.scalars().all()

    return PortalTicketListResponse(items=tickets, total=total, page=page, page_size=page_size)


@router.post("", response_model=PortalTicketOut, status_code=status.HTTP_201_CREATED)
async def submit_ticket(
    body: PortalTicketCreate,
    db: AsyncSession = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
    tenant_id: str = Depends(get_portal_tenant_id),
):
    ticket = Ticket(
        id=gen_id(),
        subject=body.subject,
        priority=TicketPriority.MEDIUM,
        requester_email=body.requester_email or customer.email,
        tenant_id=tenant_id,
        customer_id=customer.id,
    )
    db.add(ticket)

    db.add(TicketAuditLog(
        id=gen_id(),
        ticket_id=ticket.id,
        action="created",
    ))

    msg = TicketMessage(
        id=gen_id(),
        ticket_id=ticket.id,
        sender_type=SenderType.CUSTOMER,
        sender_email=customer.email,
        body_text=body.body,
        direction=MessageDirection.INBOUND,
    )
    db.add(msg)

    await _apply_sla_policies(db, ticket, tenant_id)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.post("/guest", response_model=PortalTicketOut, status_code=status.HTTP_201_CREATED)
async def submit_ticket_guest(
    body: PortalGuestTicketCreate,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = DEFAULT_TENANT_ID

    result = await db.execute(
        select(Customer).where(Customer.tenant_id == tenant_id, Customer.email == body.email)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        customer = Customer(
            id=gen_id(),
            tenant_id=tenant_id,
            email=body.email,
            display_name=body.email.split("@")[0],
            is_registered=False,
        )
        db.add(customer)
        await db.flush()

    ticket = Ticket(
        id=gen_id(),
        subject=body.subject,
        priority=TicketPriority.MEDIUM,
        requester_email=body.email,
        tenant_id=tenant_id,
        customer_id=customer.id,
    )
    db.add(ticket)

    db.add(TicketAuditLog(
        id=gen_id(),
        ticket_id=ticket.id,
        action="created",
    ))

    msg = TicketMessage(
        id=gen_id(),
        ticket_id=ticket.id,
        sender_type=SenderType.CUSTOMER,
        sender_email=body.email,
        body_text=body.body,
        direction=MessageDirection.INBOUND,
    )
    db.add(msg)

    await _apply_sla_policies(db, ticket, tenant_id)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}", response_model=PortalTicketDetailOut)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
    tenant_id: str = Depends(get_portal_tenant_id),
):
    result = await db.execute(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == tenant_id,
            Ticket.customer_id == customer.id,
        )
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.get("/{ticket_id}/messages", response_model=list[PortalMessageOut])
async def list_messages(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
    tenant_id: str = Depends(get_portal_tenant_id),
):
    ticket_result = await db.execute(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == tenant_id,
            Ticket.customer_id == customer.id,
        )
    )
    if not ticket_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Ticket not found")

    result = await db.execute(
        select(TicketMessage)
        .where(
            TicketMessage.ticket_id == ticket_id,
            TicketMessage.direction != MessageDirection.INTERNAL,
        )
        .order_by(TicketMessage.created_at)
    )
    return result.scalars().all()


@router.post("/{ticket_id}/reply", response_model=PortalMessageOut, status_code=status.HTTP_201_CREATED)
async def reply_to_ticket(
    ticket_id: str,
    body: PortalMessageCreate,
    db: AsyncSession = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
    tenant_id: str = Depends(get_portal_tenant_id),
):
    result = await db.execute(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == tenant_id,
            Ticket.customer_id == customer.id,
        )
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.status == TicketStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Ticket is closed")

    msg = TicketMessage(
        id=gen_id(),
        ticket_id=ticket_id,
        sender_type=SenderType.CUSTOMER,
        sender_email=customer.email,
        body_text=body.body_text,
        direction=MessageDirection.INBOUND,
    )
    db.add(msg)

    if ticket.status == TicketStatus.PENDING_RESPONSE:
        from app.core.state_machine import do_transition
        try:
            audit = do_transition(ticket, TicketStatus.IN_PROGRESS, None)
            db.add(audit)
        except ValueError:
            pass

    await db.commit()
    await db.refresh(msg)
    return msg


async def _apply_sla_policies(db: AsyncSession, ticket: Ticket, tenant_id: str):
    from app.models.automation import SlaPolicy, SlaTimer
    from datetime import datetime, timezone, timedelta

    result = await db.execute(
        select(SlaPolicy).where(SlaPolicy.tenant_id == tenant_id, SlaPolicy.is_active == True)
    )
    policies = result.scalars().all()

    for policy in policies:
        if _matches_sla_conditions(policy.conditions, ticket):
            now = datetime.now(timezone.utc)
            timer = SlaTimer(
                id=gen_id(),
                ticket_id=ticket.id,
                policy_id=policy.id,
                response_due_at=(
                    now + timedelta(minutes=policy.first_response_minutes)
                    if policy.first_response_minutes else None
                ),
                resolution_due_at=(
                    now + timedelta(minutes=policy.resolution_minutes)
                    if policy.resolution_minutes else None
                ),
            )
            db.add(timer)


def _matches_sla_conditions(conditions: dict, ticket: Ticket) -> bool:
    if not conditions:
        return True
    if "priority" in conditions:
        expected = conditions["priority"]
        if isinstance(expected, list):
            if ticket.priority.value not in expected:
                return False
        elif ticket.priority.value != expected:
            return False
    if "status" in conditions:
        expected = conditions["status"]
        if isinstance(expected, list):
            if ticket.status.value not in expected:
                return False
        elif ticket.status.value != expected:
            return False
    return True
