from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from services.sanity import fetch_courses, fetch_course_by_id

router = APIRouter()


def _with_match_pct(course: dict, active_tag_names: list[str]) -> dict:
    if not active_tag_names:
        return course
    course_tag_names = {t["name"] for t in (course.get("tags") or [])}
    matches = len(course_tag_names & set(active_tag_names))
    course["match_pct"] = round((matches / len(active_tag_names)) * 100)
    return course


@router.get("")
def list_courses(tags: Optional[str] = Query(None)):
    tag_names = [t.strip() for t in tags.split(",")] if tags else []
    courses = fetch_courses(tag_names if tag_names else None)
    if tag_names:
        courses = [_with_match_pct(c, tag_names) for c in courses]
        courses.sort(key=lambda c: c.get("match_pct", 0), reverse=True)
    return courses


@router.get("/{course_id}")
def get_course(course_id: str):
    course = fetch_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
