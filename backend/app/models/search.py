import enum
from datetime import datetime

from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, Enum, DateTime, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, gen_id, utcnow


class SearchIndexTicket(Base):
    __tablename__ = "search_index_tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    ticket_id: Mapped[str] = mapped_column(String(36), ForeignKey("tickets.id"), unique=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SearchIndexArticle(Base):
    __tablename__ = "search_index_articles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    article_id: Mapped[str] = mapped_column(String(36), ForeignKey("kb_articles.id"), unique=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SearchSynonym(Base, TimestampMixin):
    __tablename__ = "search_synonyms"
    __table_args__ = (
        UniqueConstraint("tenant_id", "word", name="uq_synonym_tenant_word"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    word: Mapped[str] = mapped_column(String(128))
    synonyms: Mapped[str] = mapped_column(Text)
