from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class TagWeightOut(BaseModel):
    tag_id: UUID
    weight: int

    model_config = {"from_attributes": True}


class OptionOut(BaseModel):
    id: UUID
    text: str

    model_config = {"from_attributes": True}


class QuestionOut(BaseModel):
    id: UUID
    text: str
    order: int
    options: list[OptionOut]

    model_config = {"from_attributes": True}


class QuizSubmit(BaseModel):
    answers: dict[str, str]   # { question_id: option_id }


class TagScoreOut(BaseModel):
    tag: str
    score: int
