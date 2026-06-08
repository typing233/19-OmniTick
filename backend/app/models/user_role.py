import enum

from sqlalchemy import String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, gen_id


class RoleType(str, enum.Enum):
    ADMIN = "admin"
    AGENT = "agent"
    AUTHOR = "author"
    CUSTOMER = "customer"


class UserRole(Base, TimestampMixin):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", name="uq_user_tenant_role"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    role: Mapped[RoleType] = mapped_column(Enum(RoleType))

    user = relationship("User", back_populates="roles")
    tenant = relationship("Tenant", back_populates="user_roles")
