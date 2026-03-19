import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    user_type_id = Column(UUID(as_uuid=True), ForeignKey("user_types.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    courses = relationship("TeacherCourse", back_populates="teacher", cascade="all, delete-orphan")
    user_type = relationship("UserType")
