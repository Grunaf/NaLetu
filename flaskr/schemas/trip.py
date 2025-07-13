import datetime
from typing import List
from pydantic import BaseModel, ConfigDict

from flaskr.schemas.route import DayRead
from flaskr.schemas.users import Traveler


class TripVoteDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    session_id: int
    variant_id: int
    participant_id: int
    day_order: int


class ParticipantVotesDTO(BaseModel):
    name: str
    days_with_variant: list[DayRead]


class TripSessionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    short_uuid: str
    start_date: datetime.date
    end_date: datetime.date
    departure_city_name: str


class TripSession(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    uuid: str
    route_title: str
    route_img: str
    travelers: List[Traveler]
    start_date: datetime.date
    end_date: datetime.date
    departure_city_name: str
