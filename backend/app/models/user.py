from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, gen_id


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    password_hash: Mapped[str] = mapped_column(String(256))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tenant_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tenants.id"), nullable=True, index=True
    )

    tenant = relationship("Tenant", back_populates="users")
    roles = relationship("UserRole", back_populates="user")
    assigned_tickets = relationship("Ticket", back_populates="assignee")
