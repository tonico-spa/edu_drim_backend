from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models.quiz import QuizQuestion
from schemas.quiz import QuestionOut, QuizSubmit
from services.tag_matcher import compute_tags

router = APIRouter()


@router.get("/questions", response_model=list[QuestionOut])
def get_questions(db: Session = Depends(get_db)):
    return (
        db.query(QuizQuestion)
        .options(joinedload(QuizQuestion.options))
        .order_by(QuizQuestion.order)
        .all()
    )


@router.post("/submit")
def submit_quiz(body: QuizSubmit, db: Session = Depends(get_db)):
    topic_tags, resource = compute_tags(body.answers, db)
    return {"tags": topic_tags, "resource": resource}
