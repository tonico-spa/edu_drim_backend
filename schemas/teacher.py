from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime


class TeacherRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class TeacherLogin(BaseModel):
    email: EmailStr
    password: str


class TeacherOut(BaseModel):
    id: UUID
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
