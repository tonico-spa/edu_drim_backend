import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from database import Base


class ProfessorRating(Base):
    __tablename__ = "professor_ratings"
    __table_args__ = (
        UniqueConstraint("professor_sanity_id", "teacher_id", name="uq_professor_rating_sanity_teacher"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_professor_rating_range"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    professor_sanity_id = Column(String, nullable=False, index=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
