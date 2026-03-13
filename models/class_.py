import uuid
from sqlalchemy import Column, String, Text, Integer, Boolean, Enum, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import enum


class LevelEnum(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class Class(Base):
    __tablename__ = "classes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sanity_id = Column(String, unique=True, nullable=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer)
    level = Column(Enum(LevelEnum))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    class_tags = relationship("ClassTag", back_populates="class_", cascade="all, delete-orphan")


class ClassTag(Base):
    __tablename__ = "class_tags"

    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

    class_ = relationship("Class", back_populates="class_tags")
    tag = relationship("Tag")
