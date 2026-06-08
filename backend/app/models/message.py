import enum

from sqlalchemy import String, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, gen_id


class SenderType(str, enum.Enum):
    AGENT = "agent"
    CUSTOMER = "customer"
    SYSTEM = "system"


class MessageDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"


class TicketMessage(Base, TimestampMixin):
    __tablename__ = "ticket_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    ticket_id: Mapped[str] = mapped_column(String(36), ForeignKey("tickets.id"), index=True)
    sender_type: Mapped[SenderType] = mapped_column(Enum(SenderType))
    sender_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    sender_email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    body_text: Mapped[str] = mapped_column(Text)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_message_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    email_in_reply_to: Mapped[str | None] = mapped_column(String(512), nullable=True)
    direction: Mapped[MessageDirection] = mapped_column(Enum(MessageDirection))

    ticket = relationship("Ticket", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
