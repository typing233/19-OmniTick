from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class KBCategoryCreate(BaseModel):
    name: str
    slug: str
    parent_id: Optional[str] = None
    sort_order: int = 0


class KBCategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[str] = None
    sort_order: Optional[int] = None


class KBCategoryOut(BaseModel):
    id: str
    tenant_id: str
    parent_id: Optional[str] = None
    name: str
    slug: str
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class KBCategoryTree(KBCategoryOut):
    children: list["KBCategoryTree"] = []


class KBTagCreate(BaseModel):
    name: str


class KBTagOut(BaseModel):
    id: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class KBArticleCreate(BaseModel):
    title: str
    slug: str
    body_markdown: str = ""
    body_html: str = ""
    category_id: Optional[str] = None
    visibility: str = "public"
    tag_ids: list[str] = []


class KBArticleUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    body_markdown: Optional[str] = None
    body_html: Optional[str] = None
    category_id: Optional[str] = None
    visibility: Optional[str] = None
    tag_ids: Optional[list[str]] = None
    change_summary: Optional[str] = None


class KBArticleOut(BaseModel):
    id: str
    tenant_id: str
    category_id: Optional[str] = None
    author_id: str
    title: str
    slug: str
    body_markdown: str
    body_html: str
    status: str
    visibility: str
    current_version: int
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    tags: list[KBTagOut] = []

    class Config:
        from_attributes = True


class KBArticleListOut(BaseModel):
    id: str
    title: str
    slug: str
    status: str
    visibility: str
    category_id: Optional[str] = None
    author_id: str
    current_version: int
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KBArticleListResponse(BaseModel):
    items: list[KBArticleListOut]
    total: int
    page: int
    page_size: int


class KBVersionOut(BaseModel):
    id: str
    article_id: str
    version_number: int
    title: str
    body_markdown: str
    body_html: str
    author_id: str
    change_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class KBRollbackRequest(BaseModel):
    version_number: int


class KBReviewOut(BaseModel):
    id: str
    article_id: str
    version_number: int
    reviewer_id: Optional[str] = None
    status: str
    comment: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KBReviewAction(BaseModel):
    comment: Optional[str] = None


class KBAuditLogOut(BaseModel):
    id: str
    article_id: Optional[str] = None
    actor_id: Optional[str] = None
    action: str
    detail: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
