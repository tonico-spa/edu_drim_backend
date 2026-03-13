import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from database import Base


class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    label = Column(String, nullable=False)
