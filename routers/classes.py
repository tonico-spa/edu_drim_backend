from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from services.sanity import fetch_classes, fetch_class_by_sanity_id

router = APIRouter()


def _with_match_pct(class_: dict, active_tag_names: list[str]) -> dict:
    if not active_tag_names:
        return class_
    class_tag_names = {t["name"] for t in (class_.get("tags") or [])}
    matches = len(class_tag_names & set(active_tag_names))
    class_["match_pct"] = round((matches / len(active_tag_names)) * 100)
    return class_


@router.get("")
def list_classes(
    tags: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
):
    tag_names = [t.strip() for t in tags.split(",")] if tags else []
    classes = fetch_classes(tag_names if tag_names else None, resource)
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
