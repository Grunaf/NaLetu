from pydantic import BaseModel, ConfigDict

from flaskr.schemas.route import DayRead


class TripVoteDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    session_id: int
    variant_id: int
    participant_id: int
    day_order: int


class ParticipantVotesDTO(BaseModel):
    name: str
    days_with_variant: list[DayRead]
