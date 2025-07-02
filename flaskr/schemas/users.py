import uuid
from pydantic import BaseModel, ConfigDict


class Traveler(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    uuid: uuid.UUID
    name: str
