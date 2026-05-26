from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from database import get_db
from dependencies import get_current_teacher
from models.teacher import Teacher
from models.course import TeacherCourse, TeacherCourseClass
from schemas.course import TeacherCourseCreate, TeacherCourseUpdate, TeacherCourseOut

router = APIRouter()


def _build_out(course: TeacherCourse) -> dict:
    ordered_ids = [cc.class_id for cc in sorted(course.course_classes, key=lambda x: x.order)]
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "created_at": course.created_at,
        "updated_at": course.updated_at,
        "class_ids": ordered_ids,
    }


@router.get("")
def list_teacher_courses(
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    courses = (
        db.query(TeacherCourse)
        .options(joinedload(TeacherCourse.course_classes))
        .filter(TeacherCourse.teacher_id == teacher.id)
        .all()
    )
    return [_build_out(c) for c in courses]


@router.get("/{course_id}")
def get_teacher_course(
    course_id: str,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    course = (
        db.query(TeacherCourse)
        .options(joinedload(TeacherCourse.course_classes))
        .filter(TeacherCourse.id == course_id, TeacherCourse.teacher_id == teacher.id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return _build_out(course)


@router.post("", status_code=201)
def create_teacher_course(
    body: TeacherCourseCreate,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    course = TeacherCourse(teacher_id=teacher.id, title=body.title, description=body.description)
    db.add(course)
    db.flush()

    for i, class_id in enumerate(body.class_ids):
        db.add(TeacherCourseClass(teacher_course_id=course.id, class_id=class_id, order=i))

    db.commit()
    db.refresh(course)
    return _build_out(course)


@router.put("/{course_id}")
def update_teacher_course(
    course_id: str,
    body: TeacherCourseUpdate,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    course = db.query(TeacherCourse).filter(
        TeacherCourse.id == course_id,
        TeacherCourse.teacher_id == teacher.id,
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if body.title is not None:
        course.title = body.title
    if body.description is not None:
        course.description = body.description

    if body.class_ids is not None:
        db.query(TeacherCourseClass).filter(TeacherCourseClass.teacher_course_id == course.id).delete()
        for i, class_id in enumerate(body.class_ids):
            db.add(TeacherCourseClass(teacher_course_id=course.id, class_id=class_id, order=i))

    db.commit()
    db.refresh(course)
    return _build_out(course)


@router.delete("/{course_id}", status_code=204)
def delete_teacher_course(
    course_id: str,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    course = db.query(TeacherCourse).filter(
        TeacherCourse.id == course_id,
        TeacherCourse.teacher_id == teacher.id,
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
