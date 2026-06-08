from sqlalchemy import String, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, gen_id

from datetime import datetime


class EmailAccount(Base, TimestampMixin):
    __tablename__ = "email_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    name: Mapped[str] = mapped_column(String(128))
    email_address: Mapped[str] = mapped_column(String(256), unique=True)
    imap_host: Mapped[str] = mapped_column(String(256))
    imap_port: Mapped[int] = mapped_column(Integer, default=993)
    smtp_host: Mapped[str] = mapped_column(String(256))
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    username: Mapped[str] = mapped_column(String(256))
    password_encrypted: Mapped[str] = mapped_column(String(512))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, default=60)
    last_polled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
