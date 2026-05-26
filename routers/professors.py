from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_teacher
from models.professor import ProfessorRating
from models.teacher import Teacher
from schemas.professor import RatingIn, RatingOut
from services.sanity import fetch_professors, fetch_professor_by_id

router = APIRouter()

# Bayesian average prior: assume new professors have C "phantom" ratings at the global mean M.
# Keeps a single 5-star vote from dominating the top list.
BAYESIAN_PRIOR_COUNT = 3
GLOBAL_MEAN_FALLBACK = 4.0


def _rating_aggregates(db: Session) -> dict[str, tuple[float, int]]:
    rows = (
        db.query(
            ProfessorRating.professor_sanity_id,
            func.avg(ProfessorRating.rating).label("avg_rating"),
            func.count(ProfessorRating.id).label("ratings_count"),
        )
        .group_by(ProfessorRating.professor_sanity_id)
        .all()
    )
    return {r.professor_sanity_id: (float(r.avg_rating or 0.0), int(r.ratings_count or 0)) for r in rows}


def _global_mean(db: Session) -> float:
    mean = db.query(func.avg(ProfessorRating.rating)).scalar()
    return float(mean) if mean is not None else GLOBAL_MEAN_FALLBACK


def _serialize(doc: dict, avg: float, count: int) -> dict:
    return {
        "sanity_id": doc.get("_id"),
        "name": doc.get("name"),
        "title": doc.get("title"),
        "photo_url": doc.get("photo_url"),
        "avg_rating": round(float(avg or 0.0), 2),
        "ratings_count": int(count or 0),
    }


@router.get("")
def list_professors(db: Session = Depends(get_db)):
    docs = fetch_professors()
    aggregates = _rating_aggregates(db)
    out = []
    for doc in docs:
        avg, count = aggregates.get(doc.get("_id"), (0.0, 0))
        out.append(_serialize(doc, avg, count))
    out.sort(key=lambda p: p["name"] or "")
    return out


@router.get("/top")
def top_professors(db: Session = Depends(get_db)):
    docs = fetch_professors()
    aggregates = _rating_aggregates(db)
    M = _global_mean(db)
    C = BAYESIAN_PRIOR_COUNT

    def bayesian(avg: float, count: int) -> float:
        return ((C * M) + (count * (avg or 0.0))) / (C + count)

    scored = []
    for doc in docs:
        avg, count = aggregates.get(doc.get("_id"), (0.0, 0))
        scored.append((doc, avg, count, bayesian(avg, count)))

    scored.sort(key=lambda x: x[3], reverse=True)
    return [_serialize(doc, avg, count) for doc, avg, count, _ in scored[:3]]


@router.get("/{professor_id}")
def get_professor(professor_id: str, db: Session = Depends(get_db)):
    doc = fetch_professor_by_id(professor_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Professor not found")

    avg = db.query(func.avg(ProfessorRating.rating)).filter(ProfessorRating.professor_sanity_id == professor_id).scalar() or 0.0
    count = db.query(func.count(ProfessorRating.id)).filter(ProfessorRating.professor_sanity_id == professor_id).scalar() or 0

    return {
        **_serialize(doc, avg, count),
        "bio": doc.get("bio"),
    }


@router.post("/{professor_id}/rating", response_model=RatingOut)
def rate_professor(
    professor_id: str,
    payload: RatingIn,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    doc = fetch_professor_by_id(professor_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Professor not found")

    existing = (
        db.query(ProfessorRating)
        .filter(
            ProfessorRating.professor_sanity_id == professor_id,
            ProfessorRating.teacher_id == teacher.id,
        )
        .first()
    )
    if existing:
        existing.rating = payload.rating
    else:
        db.add(ProfessorRating(professor_sanity_id=professor_id, teacher_id=teacher.id, rating=payload.rating))
    db.commit()

    avg = db.query(func.avg(ProfessorRating.rating)).filter(ProfessorRating.professor_sanity_id == professor_id).scalar() or 0.0
    count = db.query(func.count(ProfessorRating.id)).filter(ProfessorRating.professor_sanity_id == professor_id).scalar() or 0

    return RatingOut(rating=payload.rating, avg_rating=round(float(avg), 2), ratings_count=int(count))


@router.get("/{professor_id}/my-rating")
def get_my_rating(
    professor_id: str,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    r = (
        db.query(ProfessorRating)
        .filter(
            ProfessorRating.professor_sanity_id == professor_id,
            ProfessorRating.teacher_id == teacher.id,
        )
        .first()
    )
    return {"rating": r.rating if r else None}
