import enum
from datetime import datetime

from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, Enum, DateTime, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, gen_id, utcnow


class TriggerEvent(str, enum.Enum):
    ON_TICKET_CREATE = "on_ticket_create"
    ON_TICKET_UPDATE = "on_ticket_update"
    ON_STATUS_CHANGE = "on_status_change"
    ON_SLA_BREACH = "on_sla_breach"
    ON_TIME_ELAPSED = "on_time_elapsed"


class ExecutionStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class AutomationRule(Base, TimestampMixin):
    __tablename__ = "automation_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_event: Mapped[TriggerEvent] = mapped_column(Enum(TriggerEvent))
    conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    actions: Mapped[list] = mapped_column(JSON, default=list)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class AutomationExecutionLog(Base, TimestampMixin):
    __tablename__ = "automation_execution_logs"
    __table_args__ = (
        UniqueConstraint("rule_id", "ticket_id", "event_id", name="uq_automation_idempotency"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    rule_id: Mapped[str] = mapped_column(String(36), ForeignKey("automation_rules.id"), index=True)
    ticket_id: Mapped[str] = mapped_column(String(36), ForeignKey("tickets.id"), index=True)
    trigger_event: Mapped[str] = mapped_column(String(64))
    event_id: Mapped[str] = mapped_column(String(36))
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus))
    actions_executed: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_chain_depth: Mapped[int] = mapped_column(Integer, default=0)

    rule = relationship("AutomationRule")
    ticket = relationship("Ticket")


class SlaPolicy(Base, TimestampMixin):
    __tablename__ = "sla_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(256))
    conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    first_response_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SlaTimer(Base, TimestampMixin):
    __tablename__ = "sla_timers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    ticket_id: Mapped[str] = mapped_column(String(36), ForeignKey("tickets.id"), index=True)
    policy_id: Mapped[str] = mapped_column(String(36), ForeignKey("sla_policies.id"))
    response_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_met: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    resolution_met: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    breached: Mapped[bool] = mapped_column(Boolean, default=False)

    ticket = relationship("Ticket")
    policy = relationship("SlaPolicy")
