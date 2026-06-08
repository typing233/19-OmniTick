import enum
from datetime import datetime

from sqlalchemy import String, Text, Integer, ForeignKey, Enum, DateTime, Table, Column, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, gen_id, utcnow


class ArticleStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ArticleVisibility(str, enum.Enum):
    PUBLIC = "public"
    INTERNAL = "internal"


kb_article_tags = Table(
    "kb_article_tags",
    Base.metadata,
    Column("article_id", String(36), ForeignKey("kb_articles.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("kb_tags.id", ondelete="CASCADE"), primary_key=True),
)


class KBCategory(Base, TimestampMixin):
    __tablename__ = "kb_categories"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_kb_category_tenant_slug"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("kb_categories.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(256))
    slug: Mapped[str] = mapped_column(String(256))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    children = relationship("KBCategory", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("KBCategory", back_populates="children", remote_side="KBCategory.id")
    articles = relationship("KBArticle", back_populates="category")


class KBTag(Base, TimestampMixin):
    __tablename__ = "kb_tags"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_kb_tag_tenant_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))


class KBArticle(Base, TimestampMixin):
    __tablename__ = "kb_articles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_kb_article_tenant_slug"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    category_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("kb_categories.id"), nullable=True
    )
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(512))
    slug: Mapped[str] = mapped_column(String(512))
    body_markdown: Mapped[str] = mapped_column(Text, default="")
    body_html: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[ArticleStatus] = mapped_column(
        Enum(ArticleStatus), default=ArticleStatus.DRAFT, index=True
    )
    visibility: Mapped[ArticleVisibility] = mapped_column(
        Enum(ArticleVisibility), default=ArticleVisibility.PUBLIC
    )
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    category = relationship("KBCategory", back_populates="articles")
    author = relationship("User")
    tags = relationship("KBTag", secondary=kb_article_tags)
    versions = relationship("KBArticleVersion", back_populates="article", order_by="KBArticleVersion.version_number")


class KBArticleVersion(Base, TimestampMixin):
    __tablename__ = "kb_article_versions"
    __table_args__ = (
        UniqueConstraint("article_id", "version_number", name="uq_article_version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    article_id: Mapped[str] = mapped_column(String(36), ForeignKey("kb_articles.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(512))
    body_markdown: Mapped[str] = mapped_column(Text)
    body_html: Mapped[str] = mapped_column(Text, default="")
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    change_summary: Mapped[str | None] = mapped_column(String(512), nullable=True)

    article = relationship("KBArticle", back_populates="versions")
    author = relationship("User")


class KBReview(Base, TimestampMixin):
    __tablename__ = "kb_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    article_id: Mapped[str] = mapped_column(String(36), ForeignKey("kb_articles.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    reviewer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    article = relationship("KBArticle")
    reviewer = relationship("User")


class KBAuditLog(Base, TimestampMixin):
    __tablename__ = "kb_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    article_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("kb_articles.id"), nullable=True
    )
    actor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(64))
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    article = relationship("KBArticle")
    actor = relationship("User")
