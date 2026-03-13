from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from database import get_db
from models.teacher import Teacher
from schemas.teacher import TeacherRegister, TeacherLogin, TeacherOut, TokenOut, ForgotPasswordRequest, ResetPasswordRequest
import os

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12, bcrypt__truncate_error=False)
SECRET_KEY = os.getenv("JWT_SECRET", "dev_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h


def create_token(teacher_id: str, name: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": teacher_id, "name": name, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: TeacherRegister, db: Session = Depends(get_db)):
    if db.query(Teacher).filter(Teacher.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    teacher = Teacher(
        name=body.name,
        email=body.email,
        password_hash=pwd_context.hash(body.password),
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return {"access_token": create_token(str(teacher.id), teacher.name)}


@router.post("/login", response_model=TokenOut)
def login(body: TeacherLogin, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.email == body.email).first()
    if not teacher or not pwd_context.verify(body.password, teacher.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_token(str(teacher.id), teacher.name)}


@router.post("/forgot-password", status_code=200)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # In production: generate a reset token, store it, and send an email.
    # Returning 200 regardless to prevent email enumeration.
    teacher = db.query(Teacher).filter(Teacher.email == body.email).first()
    if teacher:
        reset_token = create_token(str(teacher.id), teacher.name)
        # TODO: send email with reset_token
    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password", status_code=200)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(body.token, SECRET_KEY, algorithms=[ALGORITHM])
        teacher_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    teacher.password_hash = pwd_context.hash(body.password)
    db.commit()
    return {"message": "Password updated successfully"}
