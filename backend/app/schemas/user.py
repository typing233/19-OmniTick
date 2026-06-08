from pydantic import BaseModel
from datetime import datetime


class UserOut(BaseModel):
    id: str
    email: str
    display_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str
    display_name: str
    password: str
