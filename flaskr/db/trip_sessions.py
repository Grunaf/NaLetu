import uuid
from datetime import datetime

from sqlalchemy import delete, select

from flaskr.models.models import db
from flaskr.models.trip import TripSession


def get_trip_session_by_uuid(session_uuid: uuid.UUID) -> TripSession | None:
    stmt = select(TripSession).where(TripSession.uuid == session_uuid)
    return db.session.execute(stmt).scalar()


def get_trip_session_by_id(id: int) -> TripSession | None:
    stmt = select(TripSession).where(TripSession.id == id)
    return db.session.execute(stmt).scalar()


def delete_trip_session(session_uuid: uuid.UUID) -> int:
    stmt = delete(TripSession).where(TripSession.uuid == session_uuid)
    result = db.session.execute(stmt)
    db.session.commit()
    return result.rowcount


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
