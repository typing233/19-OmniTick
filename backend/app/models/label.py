from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, gen_id
from .ticket import ticket_labels


class Label(Base, TimestampMixin):
    __tablename__ = "labels"
    __table_args__ = (
        UniqueConstraint("name", "tenant_id", name="uq_label_name_tenant"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    name: Mapped[str] = mapped_column(String(64))
    color: Mapped[str] = mapped_column(String(7), default="#1677ff")
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id"), index=True
    )

    tickets = relationship("Ticket", secondary=ticket_labels, back_populates="labels")
