import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class CatalogCourse(Base):
    __tablename__ = "catalog_courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course_classes = relationship("CatalogCourseClass", back_populates="course", cascade="all, delete-orphan")
    course_tags = relationship("CatalogCourseTag", back_populates="course", cascade="all, delete-orphan")


class CatalogCourseClass(Base):
    __tablename__ = "catalog_course_classes"

    catalog_course_id = Column(UUID(as_uuid=True), ForeignKey("catalog_courses.id", ondelete="CASCADE"), primary_key=True)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True)
    order = Column(Integer, default=0)

    course = relationship("CatalogCourse", back_populates="course_classes")
    class_ = relationship("Class")


class CatalogCourseTag(Base):
    __tablename__ = "catalog_course_tags"

    catalog_course_id = Column(UUID(as_uuid=True), ForeignKey("catalog_courses.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

    course = relationship("CatalogCourse", back_populates="course_tags")
    tag = relationship("Tag")


class TeacherCourse(Base):
    __tablename__ = "teacher_courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    teacher = relationship("Teacher", back_populates="courses")
    course_classes = relationship("TeacherCourseClass", back_populates="course", cascade="all, delete-orphan")


class TeacherCourseClass(Base):
    __tablename__ = "teacher_course_classes"

    teacher_course_id = Column(UUID(as_uuid=True), ForeignKey("teacher_courses.id", ondelete="CASCADE"), primary_key=True)
    class_id = Column(String, primary_key=True)   # Sanity document ID
    order = Column(Integer, default=0)

    course = relationship("TeacherCourse", back_populates="course_classes")
