from pydantic import BaseModel
from uuid import UUID


class UserTypeOut(BaseModel):
    id: UUID
    slug: str
    label: str

    model_config = {"from_attributes": True}
