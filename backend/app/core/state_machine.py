from typing import Dict, Set

from app.models.ticket import TicketStatus
from app.models.audit import TicketAuditLog
from app.models.base import gen_id

TRANSITIONS: Dict[TicketStatus, Set[TicketStatus]] = {
    TicketStatus.NEW: {TicketStatus.IN_PROGRESS, TicketStatus.CLOSED},
    TicketStatus.IN_PROGRESS: {
        TicketStatus.PENDING_RESPONSE,
        TicketStatus.RESOLVED,
        TicketStatus.CLOSED,
    },
    TicketStatus.PENDING_RESPONSE: {
        TicketStatus.IN_PROGRESS,
        TicketStatus.RESOLVED,
        TicketStatus.CLOSED,
    },
    TicketStatus.RESOLVED: {TicketStatus.IN_PROGRESS, TicketStatus.CLOSED},
    TicketStatus.CLOSED: {TicketStatus.IN_PROGRESS},
}


def can_transition(from_status: TicketStatus, to_status: TicketStatus) -> bool:
    return to_status in TRANSITIONS.get(from_status, set())


def do_transition(ticket, to_status: TicketStatus, actor_id: str | None) -> TicketAuditLog:
    if not can_transition(ticket.status, to_status):
        raise ValueError(
            f"Cannot transition from '{ticket.status.value}' to '{to_status.value}'"
        )
    old_status = ticket.status
    ticket.status = to_status
    return TicketAuditLog(
        id=gen_id(),
        ticket_id=ticket.id,
        actor_id=actor_id,
        action="status_change",
        field_name="status",
        old_value=old_status.value,
        new_value=to_status.value,
    )


def get_allowed_transitions(status: TicketStatus) -> list[TicketStatus]:
    return list(TRANSITIONS.get(status, set()))
