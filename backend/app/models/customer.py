from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, gen_id


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_customer_tenant_email"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id"), index=True
    )
    email: Mapped[str] = mapped_column(String(256), index=True)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_registered: Mapped[bool] = mapped_column(Boolean, default=False)

    tenant = relationship("Tenant")
    tickets = relationship("Ticket", back_populates="customer")
