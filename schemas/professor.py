from pydantic import BaseModel, Field
from typing import Optional


class ProfessorOut(BaseModel):
    sanity_id: str
    name: str
    title: Optional[str] = None
    photo_url: Optional[str] = None
    avg_rating: float
    ratings_count: int


class RatingIn(BaseModel):
    rating: int = Field(ge=1, le=5)


class RatingOut(BaseModel):
    rating: int
    avg_rating: float
    ratings_count: int
