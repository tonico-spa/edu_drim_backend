from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime


class TagOut(BaseModel):
    id: UUID
    name: str
    label: str

    model_config = {"from_attributes": True}


class ClassOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    duration_minutes: Optional[int]
    level: Optional[str]
    is_active: bool
    tags: list[TagOut] = []

    model_config = {"from_attributes": True}
