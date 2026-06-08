from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CustomerRegister(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None


class CustomerLogin(BaseModel):
    email: str
    password: str


class CustomerTokenResponse(BaseModel):
    access_token: str


class CustomerOut(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None
    is_registered: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PortalTicketCreate(BaseModel):
    subject: str
    body: str
    requester_email: Optional[str] = None


class PortalTicketOut(BaseModel):
    id: str
    subject: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortalTicketDetailOut(PortalTicketOut):
    requester_email: Optional[str] = None


class PortalTicketListResponse(BaseModel):
    items: list[PortalTicketOut]
    total: int
    page: int
    page_size: int


class PortalMessageCreate(BaseModel):
    body_text: str


class PortalMessageOut(BaseModel):
    id: str
    sender_type: str
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PortalArticleOut(BaseModel):
    id: str
    title: str
    slug: str
    body_html: str
    category_id: Optional[str] = None
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PortalArticleListResponse(BaseModel):
    items: list[PortalArticleOut]
    total: int
    page: int
    page_size: int
