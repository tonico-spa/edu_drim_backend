from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime
from schemas.class_ import ClassOut, TagOut


class CatalogCourseOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    tags: list[TagOut] = []
    classes: list[ClassOut] = []
    match_pct: Optional[int] = None

    model_config = {"from_attributes": True}


class TeacherCourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    class_ids: list[str]  # Sanity document IDs


class TeacherCourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    class_ids: Optional[list[str]] = None  # Sanity document IDs


class TeacherCourseOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    classes: list[ClassOut] = []

    model_config = {"from_attributes": True}
