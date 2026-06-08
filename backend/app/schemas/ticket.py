from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.models.ticket import TicketStatus, TicketPriority


class TicketCreate(BaseModel):
    subject: str
    priority: TicketPriority = TicketPriority.MEDIUM
    assignee_id: Optional[str] = None
    requester_email: Optional[str] = None
    body: Optional[str] = None
    label_ids: list[str] = []


class TicketUpdate(BaseModel):
    subject: Optional[str] = None
    priority: Optional[TicketPriority] = None
    requester_email: Optional[str] = None
    email_account_id: Optional[str] = None


class TicketTransition(BaseModel):
    status: TicketStatus


class TicketAssign(BaseModel):
    assignee_id: Optional[str] = None


class TicketLabelAttach(BaseModel):
    label_ids: list[str]


class LabelBrief(BaseModel):
    id: str
    name: str
    color: str

    class Config:
        from_attributes = True


class AssigneeBrief(BaseModel):
    id: str
    display_name: str
    email: str

    class Config:
        from_attributes = True


class TicketOut(BaseModel):
    id: str
    subject: str
    status: TicketStatus
    priority: TicketPriority
    assignee_id: Optional[str] = None
    assignee: Optional[AssigneeBrief] = None
    requester_email: Optional[str] = None
    email_account_id: Optional[str] = None
    labels: list[LabelBrief] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    items: list[TicketOut]
    total: int
    page: int
    page_size: int
