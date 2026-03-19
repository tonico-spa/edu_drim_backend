import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from database import Base


class UserType(Base):
    __tablename__ = "user_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String, unique=True, nullable=False)
    label = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
