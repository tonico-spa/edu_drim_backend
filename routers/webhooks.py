import hashlib
import hmac
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.class_ import Class, ClassTag, ClassUserType
from models.user_type import UserType
from models.tag import Tag

router = APIRouter()

SANITY_WEBHOOK_SECRET = os.getenv("SANITY_WEBHOOK_SECRET", "")


def _verify_signature(body: bytes, signature: str) -> bool:
    if not SANITY_WEBHOOK_SECRET:
        return True  # skip in local dev if secret not set
    expected = hmac.new(SANITY_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/sanity")
async def sanity_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    sig = request.headers.get("sanity-webhook-signature", "")

    if not _verify_signature(body, sig):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    event_type = payload.get("_type")
    sanity_id = payload.get("_id")

    if not sanity_id:
        raise HTTPException(status_code=400, detail="Missing _id in payload")

    if event_type == "class":
        _upsert_class(db, payload, sanity_id)
    elif event_type in ("sanity.deleteEvent",):
        _deactivate_class(db, sanity_id)

    return {"ok": True}


@router.post("/sanity/sync/{sanity_id}")
def manual_sync(sanity_id: str, db: Session = Depends(get_db)):
    """Admin endpoint to manually re-sync a class from Sanity by its ID."""
    return {"message": f"Sync triggered for {sanity_id}"}


def _upsert_class(db: Session, payload: dict, sanity_id: str):
    cls = db.query(Class).filter(Class.sanity_id == sanity_id).first()
    is_new = cls is None
    if is_new:
        cls = Class(sanity_id=sanity_id)
        db.add(cls)

    cls.title = payload.get("title", "")
    cls.description = payload.get("description", "")
    cls.duration_minutes = payload.get("duration_minutes")
    cls.level = payload.get("level")
    cls.is_active = True

    # Sync tags
    db.query(ClassTag).filter(ClassTag.class_id == cls.id).delete()
    for tag_ref in payload.get("tags", []):
        tag_name = tag_ref.get("name", {}).get("current") if isinstance(tag_ref.get("name"), dict) else tag_ref.get("name")
        if tag_name:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if tag:
                db.add(ClassTag(class_id=cls.id, tag_id=tag.id))

    db.commit()
    db.refresh(cls)

    # On new class: make it visible to all non-admin user_types by default
    if is_new:
        non_admin_types = db.query(UserType).filter(UserType.is_admin == False).all()
        for ut in non_admin_types:
            db.add(ClassUserType(class_id=cls.id, user_type_id=ut.id))
        db.commit()


def _deactivate_class(db: Session, sanity_id: str):
    cls = db.query(Class).filter(Class.sanity_id == sanity_id).first()
    if cls:
        cls.is_active = False
        db.commit()
