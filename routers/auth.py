from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from database import get_db
from models.teacher import Teacher
from models.user_type import UserType
from schemas.teacher import TeacherRegister, TeacherLogin, TeacherOut, TokenOut, ForgotPasswordRequest, ResetPasswordRequest
import os

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12, bcrypt__truncate_error=False)
SECRET_KEY = os.getenv("JWT_SECRET", "dev_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h


def create_token(teacher_id: str, name: str, user_type_id: str | None, is_admin: bool) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": teacher_id, "name": name, "user_type_id": user_type_id, "is_admin": is_admin, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: TeacherRegister, db: Session = Depends(get_db)):
    if db.query(Teacher).filter(Teacher.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Resolve user_type — must not be admin
    user_type = None
    if body.user_type_id:
        user_type = db.query(UserType).filter(UserType.id == body.user_type_id).first()
        if not user_type:
            raise HTTPException(status_code=400, detail="Invalid user type")
        if user_type.is_admin:
            raise HTTPException(status_code=400, detail="Cannot self-register as admin")
    else:
        # Default: first non-admin type
        user_type = db.query(UserType).filter(UserType.is_admin == False).first()

    teacher = Teacher(
        name=body.name,
        email=body.email,
        password_hash=pwd_context.hash(body.password),
        user_type_id=user_type.id if user_type else None,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    is_admin = user_type.is_admin if user_type else False
    user_type_id_str = str(user_type.id) if user_type else None
    return {"access_token": create_token(str(teacher.id), teacher.name, user_type_id_str, is_admin)}


@router.post("/login", response_model=TokenOut)
def login(body: TeacherLogin, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.email == body.email).first()
    if not teacher or not pwd_context.verify(body.password, teacher.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_type = db.query(UserType).filter(UserType.id == teacher.user_type_id).first() if teacher.user_type_id else None
    is_admin = user_type.is_admin if user_type else False
    user_type_id_str = str(teacher.user_type_id) if teacher.user_type_id else None
    return {"access_token": create_token(str(teacher.id), teacher.name, user_type_id_str, is_admin)}


@router.post("/forgot-password", status_code=200)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.email == body.email).first()
    if teacher:
        user_type = db.query(UserType).filter(UserType.id == teacher.user_type_id).first() if teacher.user_type_id else None
        is_admin = user_type.is_admin if user_type else False
        reset_token = create_token(str(teacher.id), teacher.name, str(teacher.user_type_id) if teacher.user_type_id else None, is_admin)
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
