from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, gen_id
from .ticket import ticket_labels


class Label(Base, TimestampMixin):
    __tablename__ = "labels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    color: Mapped[str] = mapped_column(String(7), default="#1677ff")

    tickets = relationship("Ticket", secondary=ticket_labels, back_populates="labels")
