from pydantic import BaseModel
from pydantic import ConfigDict


class City(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: int
    name: str
    lat: float
    lon: float
    slug: str
