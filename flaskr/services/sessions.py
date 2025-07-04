from typing import List
import uuid

import shortuuid
from flaskr.db.participations import (
    get_session_named_participations,
    get_traveler_participations,
)
from flaskr.models.trip import TripParticipant
from flaskr.schemas.trip import TripSession
from flaskr.schemas.users import Traveler


def get_trip_session_travelers(
    traveler_uuid: uuid.UUID, session_id: int
) -> List[Traveler]:
    participations: List[TripParticipant] = get_session_named_participations(session_id)
    return [
        Traveler.model_validate(participation.user)
        for participation in participations
        if participation.user_uuid != traveler_uuid
    ]


def get_traveler_trip_sessions(traveler_uuid: uuid.UUID) -> List[TripSession]:
    participations = get_traveler_participations(traveler_uuid)
    sessions = []
    for participation in participations:
        session = participation.session

        route_title = session.route.title
        route_img = session.route.img
        travelers = get_trip_session_travelers(
            participation.user_uuid, participation.session_id
        )
        departure_city_name = session.city.name
        short_uuid = shortuuid.encode(session.uuid)

        session_read = TripSession(
            uuid=short_uuid,
            start_date=session.start_date,
            end_date=session.end_date,
            route_title=route_title,
            route_img=route_img,
            travelers=travelers,
            departure_city_name=departure_city_name,
        )
        sessions.append(session_read)
    return sessions
