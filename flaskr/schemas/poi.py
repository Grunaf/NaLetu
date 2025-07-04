import datetime
from pydantic import BaseModel, ConfigDict


class POI(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: int
    name: str
    must_see: bool
    open_time: datetime.time
    close_time: datetime.time
    rating: float | None = None
    lat: float
    lon: float
