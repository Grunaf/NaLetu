import uuid

from sqlalchemy import select
from flaskr.models.models import db
from flaskr.models.trip import TripParticipant, TripSession


def get_trip_session_where_user_admin(user_uuid: uuid.UUID):
    stmt = (
            select(TripParticipant)
            .where(TripParticipant.user_uuid == user_uuid)
            .where(TripParticipant.is_admin)
        )

    return db.session.execute(stmt).scalars().all()


def get_trip_session_by_uuid(session_uuid: uuid.UUID):
    stmt = select(TripSession).where(TripSession.uuid == session_uuid)
    return db.session.execute(stmt).scalars().first()


def get_trip_session_by_id(id: int):
    stmt = select(TripSession).where(TripSession.id == id)
    return db.session.execute(stmt).scalars().first()
