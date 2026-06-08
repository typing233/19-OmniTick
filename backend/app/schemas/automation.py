from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AutomationRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_event: str
    conditions: dict = {}
    actions: list = []
    priority: int = 0
    is_active: bool = True


class AutomationRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_event: Optional[str] = None
    conditions: Optional[dict] = None
    actions: Optional[list] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class AutomationRuleOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    trigger_event: str
    conditions: dict
    actions: list
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AutomationLogOut(BaseModel):
    id: str
    rule_id: str
    ticket_id: str
    trigger_event: str
    event_id: str
    status: str
    actions_executed: Optional[dict] = None
    error_detail: Optional[str] = None
    execution_chain_depth: int
    created_at: datetime

    class Config:
        from_attributes = True


class AutomationLogListResponse(BaseModel):
    items: list[AutomationLogOut]
    total: int
    page: int
    page_size: int


class SlaPolicyCreate(BaseModel):
    name: str
    conditions: dict = {}
    first_response_minutes: Optional[int] = None
    resolution_minutes: Optional[int] = None
    is_active: bool = True


class SlaPolicyUpdate(BaseModel):
    name: Optional[str] = None
    conditions: Optional[dict] = None
    first_response_minutes: Optional[int] = None
    resolution_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class SlaPolicyOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    conditions: dict
    first_response_minutes: Optional[int] = None
    resolution_minutes: Optional[int] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
