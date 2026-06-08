from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.models.message import SenderType, MessageDirection


class MessageCreate(BaseModel):
    body_text: str
    body_html: Optional[str] = None
    direction: MessageDirection = MessageDirection.OUTBOUND


class MessageOut(BaseModel):
    id: str
    ticket_id: str
    sender_type: SenderType
    sender_id: Optional[str] = None
    sender_email: Optional[str] = None
    body_text: str
    body_html: Optional[str] = None
    direction: MessageDirection
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogOut(BaseModel):
    id: str
    ticket_id: str
    actor_id: Optional[str] = None
    action: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
