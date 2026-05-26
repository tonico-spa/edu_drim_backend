from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from models.class_ import Class, ClassUserType
from services.sanity import fetch_classes, fetch_class_by_sanity_id
from dependencies import get_optional_teacher

router = APIRouter()


def _with_match_pct(class_: dict, active_tag_names: list[str]) -> dict:
    if not active_tag_names:
        return class_
    class_tag_names = {t["name"] for t in (class_.get("tags") or [])}
    matches = len(class_tag_names & set(active_tag_names))
    class_["match_pct"] = round((matches / len(active_tag_names)) * 100)
    return class_


def _get_allowed_sanity_ids(user_type_id: str, db: Session) -> Optional[set]:
    """Returns the set of sanity_ids allowed for this user_type, or None if no restrictions."""
    rows = (
        db.query(Class.sanity_id)
        .join(ClassUserType, ClassUserType.class_id == Class.id)
        .filter(ClassUserType.user_type_id == user_type_id)
        .filter(Class.sanity_id.isnot(None))
        .all()
    )
    return {r.sanity_id for r in rows}


@router.get("/allowed-ids")
def get_allowed_ids(
    teacher=Depends(get_optional_teacher),
    db: Session = Depends(get_db),
):
    """Returns the sanity_ids the current teacher is allowed to see.
    Returns null if no restriction applies (not logged in, or admin)."""
    if not teacher or teacher.get("is_admin") or not teacher.get("user_type_id"):
        return {"ids": None}
    ids = _get_allowed_sanity_ids(teacher["user_type_id"], db)
    return {"ids": list(ids)}


@router.get("")
def list_classes(
    tags: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    teacher=Depends(get_optional_teacher),
    db: Session = Depends(get_db),
):
    tag_names = [t.strip() for t in tags.split(",")] if tags else []
    classes = fetch_classes(tag_names if tag_names else None, resource)

    # Filter by user_type if logged in and not admin
    if teacher and not teacher.get("is_admin") and teacher.get("user_type_id"):
        allowed = _get_allowed_sanity_ids(teacher["user_type_id"], db)
        classes = [c for c in classes if c.get("_id") in allowed]

    if tag_names:
        classes = [_with_match_pct(c, tag_names) for c in classes]
        classes.sort(key=lambda c: c.get("match_pct", 0), reverse=True)
    return classes


@router.get("/{class_id}")
def get_class(class_id: str):
    class_ = fetch_class_by_sanity_id(class_id)
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_
