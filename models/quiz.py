import uuid
from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    order = Column(Integer, default=0)

    options = relationship("QuizOption", back_populates="question", cascade="all, delete-orphan")


class QuizOption(Base):
    __tablename__ = "quiz_options"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)
    text = Column(String, nullable=False)

    question = relationship("QuizQuestion", back_populates="options")
    tag_weights = relationship("QuizOptionTagWeight", back_populates="option", cascade="all, delete-orphan")


class QuizOptionTagWeight(Base):
    __tablename__ = "quiz_option_tag_weights"

    option_id = Column(UUID(as_uuid=True), ForeignKey("quiz_options.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    weight = Column(Integer, default=1)

    option = relationship("QuizOption", back_populates="tag_weights")
    tag = relationship("Tag")
