from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ContactRequestCreate(BaseModel):
    message: str = Field(..., min_length=10, max_length=2000)


class ContactRequestStatusUpdate(BaseModel):
    status: str  # 'new', 'read', 'closed'


class ContactItemBrief(BaseModel):
    id: int
    reference_code: str
    title: str
    status: str
    primary_image: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ContactUserBrief(BaseModel):
    id: int
    full_name: str
    department: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ContactRequestOut(BaseModel):
    id: int
    item_id: int
    item: ContactItemBrief
    sender: ContactUserBrief
    recipient: ContactUserBrief
    message: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
