from pydantic import BaseModel
from datetime import datetime


class LabelOut(BaseModel):
    id: str
    name: str
    color: str
    created_at: datetime

    class Config:
        from_attributes = True


class LabelCreate(BaseModel):
    name: str
    color: str = "#1677ff"


class LabelUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
