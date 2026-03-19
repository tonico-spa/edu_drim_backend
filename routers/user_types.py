from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.user_type import UserType
from schemas.user_type import UserTypeOut

router = APIRouter()


@router.get("", response_model=List[UserTypeOut])
def list_user_types(db: Session = Depends(get_db)):
    """Returns all user types except admin — used to populate the register form."""
    return db.query(UserType).filter(UserType.is_admin == False).all()
