from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, gen_id


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    name: Mapped[str] = mapped_column(String(256))
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    users = relationship("User", back_populates="tenant")
    user_roles = relationship("UserRole", back_populates="tenant")
