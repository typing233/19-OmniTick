from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, gen_id


class TicketAuditLog(Base, TimestampMixin):
    __tablename__ = "ticket_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    ticket_id: Mapped[str] = mapped_column(String(36), ForeignKey("tickets.id"), index=True)
    actor_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(64))
    field_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    old_value: Mapped[str | None] = mapped_column(String(512), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(512), nullable=True)

    ticket = relationship("Ticket", back_populates="audit_logs")
    actor = relationship("User", foreign_keys=[actor_id])
