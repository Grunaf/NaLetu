from datetime import datetime
from typing import List
import uuid

from sqlalchemy import select
from flaskr.models.models import db
from flaskr.models.trip import TripParticipant, TripSession


def get_admin_participants(user_uuid: uuid.UUID) -> List[TripParticipant]:
    stmt = (
        select(TripParticipant)
        .where(TripParticipant.user_uuid == user_uuid)
        .where(TripParticipant.is_admin)
    )

    return list(db.session.execute(stmt).scalars().all())


def get_trip_session_by_uuid(session_uuid: uuid.UUID) -> TripParticipant | None:
    stmt = select(TripSession).where(TripSession.uuid == session_uuid)
    return db.session.execute(stmt).scalar()


def get_trip_session_by_id(id: int) -> TripParticipant | None:
    stmt = select(TripSession).where(TripSession.id == id)
    return db.session.execute(stmt).scalar()


def create_trip_session(
    route_id: int, departure_city_id: int, start_date: datetime, end_date: datetime
) -> TripSession:
    trip_session = TripSession(
        route_id=route_id,
        departure_city_id=departure_city_id,
        start_date=start_date,
        end_date=end_date,
    )

    db.session.add(trip_session)
    db.session.commit()
    return trip_session
