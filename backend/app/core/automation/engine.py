import logging
import hashlib
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.ticket import Ticket, TicketStatus, TicketPriority
from app.models.label import Label
from app.models.audit import TicketAuditLog
from app.models.automation import (
    AutomationRule, AutomationExecutionLog, TriggerEvent, ExecutionStatus,
)
from app.models.base import gen_id
from app.core.state_machine import do_transition

logger = logging.getLogger(__name__)

MAX_CHAIN_DEPTH = 5


def generate_event_id(ticket_id: str, trigger_event: str, timestamp: datetime) -> str:
    bucket = timestamp.strftime("%Y%m%d%H%M")
    raw = f"{ticket_id}:{trigger_event}:{bucket}"
    return hashlib.sha256(raw.encode()).hexdigest()[:36]


def evaluate_conditions(ticket: Ticket, conditions: dict) -> bool:
    if not conditions:
        return True

    for field, matcher in conditions.items():
        if field == "status":
            if isinstance(matcher, list):
                if ticket.status.value not in matcher:
                    return False
            elif ticket.status.value != matcher:
                return False
        elif field == "priority":
            if isinstance(matcher, list):
                if ticket.priority.value not in matcher:
                    return False
            elif ticket.priority.value != matcher:
                return False
        elif field == "assignee_id":
            if matcher == "unassigned":
                if ticket.assignee_id is not None:
                    return False
            elif ticket.assignee_id != matcher:
                return False
        elif field == "labels":
            ticket_label_names = [l.name for l in ticket.labels] if ticket.labels else []
            if isinstance(matcher, dict):
                if "contains" in matcher:
                    if matcher["contains"] not in ticket_label_names:
                        return False
                if "not_contains" in matcher:
                    if matcher["not_contains"] in ticket_label_names:
                        return False
            elif isinstance(matcher, list):
                if not any(l in ticket_label_names for l in matcher):
                    return False
    return True


async def execute_actions(
    db: AsyncSession, ticket: Ticket, actions: list, tenant_id: str
) -> list[dict]:
    executed = []
    for action in actions:
        action_type = action.get("type")
        params = action.get("params", {})

        try:
            if action_type == "assign":
                ticket.assignee_id = params.get("assignee_id")
                db.add(TicketAuditLog(
                    id=gen_id(), ticket_id=ticket.id,
                    action="assign", field_name="assignee_id",
                    new_value=params.get("assignee_id"),
                ))
                executed.append({"type": "assign", "status": "ok"})

            elif action_type == "change_status":
                target = TicketStatus(params["status"])
                try:
                    audit = do_transition(ticket, target, None)
                    db.add(audit)
                    executed.append({"type": "change_status", "status": "ok"})
                except ValueError as e:
                    executed.append({"type": "change_status", "status": "skipped", "reason": str(e)})

            elif action_type == "change_priority":
                ticket.priority = TicketPriority(params["priority"])
                db.add(TicketAuditLog(
                    id=gen_id(), ticket_id=ticket.id,
                    action="field_change", field_name="priority",
                    new_value=params["priority"],
                ))
                executed.append({"type": "change_priority", "status": "ok"})

            elif action_type == "add_label":
                label_result = await db.execute(
                    select(Label).where(Label.name == params["label_name"], Label.tenant_id == tenant_id)
                )
                label = label_result.scalar_one_or_none()
                if label and label not in (ticket.labels or []):
                    ticket.labels.append(label)
                    db.add(TicketAuditLog(
                        id=gen_id(), ticket_id=ticket.id,
                        action="label_add", field_name="labels",
                        new_value=label.name,
                    ))
                executed.append({"type": "add_label", "status": "ok"})

            elif action_type == "notify":
                executed.append({"type": "notify", "status": "ok", "target": params.get("target")})

            elif action_type == "escalate":
                ticket.priority = TicketPriority.URGENT
                db.add(TicketAuditLog(
                    id=gen_id(), ticket_id=ticket.id,
                    action="field_change", field_name="priority",
                    old_value=ticket.priority.value, new_value="urgent",
                ))
                if params.get("assignee_id"):
                    ticket.assignee_id = params["assignee_id"]
                executed.append({"type": "escalate", "status": "ok"})

            else:
                executed.append({"type": action_type, "status": "unknown_action"})

        except Exception as e:
            executed.append({"type": action_type, "status": "error", "error": str(e)})

    return executed


async def run_automation(
    db: AsyncSession,
    ticket: Ticket,
    trigger_event: TriggerEvent,
    tenant_id: str,
    chain_depth: int = 0,
):
    if chain_depth >= MAX_CHAIN_DEPTH:
        logger.warning(f"Automation chain depth exceeded for ticket {ticket.id}")
        return

    event_id = generate_event_id(ticket.id, trigger_event.value, datetime.now(timezone.utc))

    rules_result = await db.execute(
        select(AutomationRule).where(
            AutomationRule.tenant_id == tenant_id,
            AutomationRule.trigger_event == trigger_event,
            AutomationRule.is_active == True,
        ).order_by(AutomationRule.priority)
    )
    rules = rules_result.scalars().all()

    if not rules:
        return

    if ticket.labels is None:
        await db.refresh(ticket, ["labels"])

    for rule in rules:
        existing = await db.execute(
            select(AutomationExecutionLog).where(
                AutomationExecutionLog.rule_id == rule.id,
                AutomationExecutionLog.ticket_id == ticket.id,
                AutomationExecutionLog.event_id == event_id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        if not evaluate_conditions(ticket, rule.conditions):
            db.add(AutomationExecutionLog(
                id=gen_id(),
                rule_id=rule.id,
                ticket_id=ticket.id,
                trigger_event=trigger_event.value,
                event_id=event_id,
                status=ExecutionStatus.SKIPPED,
                execution_chain_depth=chain_depth,
            ))
            continue

        try:
            executed = await execute_actions(db, ticket, rule.actions, tenant_id)
            db.add(AutomationExecutionLog(
                id=gen_id(),
                rule_id=rule.id,
                ticket_id=ticket.id,
                trigger_event=trigger_event.value,
                event_id=event_id,
                status=ExecutionStatus.SUCCESS,
                actions_executed={"actions": executed},
                execution_chain_depth=chain_depth,
            ))
        except Exception as e:
            db.add(AutomationExecutionLog(
                id=gen_id(),
                rule_id=rule.id,
                ticket_id=ticket.id,
                trigger_event=trigger_event.value,
                event_id=event_id,
                status=ExecutionStatus.FAILED,
                error_detail=str(e),
                execution_chain_depth=chain_depth,
            ))
            logger.error(f"Automation rule {rule.id} failed: {e}")
