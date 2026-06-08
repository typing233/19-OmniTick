import enum
from datetime import datetime

from sqlalchemy import String, ForeignKey, Table, Column, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, gen_id, utcnow


class TicketStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    PENDING_RESPONSE = "pending_response"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


ticket_labels = Table(
    "ticket_labels",
    Base.metadata,
    Column("ticket_id", String(36), ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", String(36), ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    subject: Mapped[str] = mapped_column(String(512))
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus), default=TicketStatus.NEW, index=True
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority), default=TicketPriority.MEDIUM
    )
    assignee_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    requester_email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    email_message_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    email_account_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("email_accounts.id"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    assignee = relationship("User", back_populates="assigned_tickets")
    labels = relationship("Label", secondary=ticket_labels, back_populates="tickets")
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketMessage.created_at")
    audit_logs = relationship("TicketAuditLog", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketAuditLog.created_at")
