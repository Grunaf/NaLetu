from typing import List
import uuid

from sqlalchemy import select

from flaskr.models.models import db
from flaskr.models.trip import TripParticipant
from flaskr.models.user import Traveler


def get_session_named_participations(session_id: int) -> List[TripParticipant]:
    criteria = [
        TripParticipant.session_id == session_id,
        Traveler.name.isnot(None),
    ]
    stmt = select(TripParticipant).join(TripParticipant.user).filter(*criteria)
    return list(db.session.execute(stmt).scalars().all())


def is_many_travelers_in_session(session_id: int) -> bool:
    stmt = select(TripParticipant).filter(TripParticipant.session_id == session_id)
    participations = db.session.execute(stmt).scalars().all()
    return len(participations) > 1


def create_participant(
    user_uuid: uuid.UUID, session_id: int, is_admin: bool = False
) -> TripParticipant:
    participant = TripParticipant(
        user_uuid=user_uuid, session_id=session_id, is_admin=is_admin
    )
    db.session.add(participant)
    db.session.commit()
    return participant


def get_session_participations(session_id: int) -> List[TripParticipant]:
    stmt = select(TripParticipant).where(TripParticipant.session_id == session_id)
    return list(db.session.execute(stmt).scalars().all())


def get_traveler_participations(user_uuid: uuid.UUID) -> List[TripParticipant]:
    stmt = select(TripParticipant).where(TripParticipant.user_uuid == user_uuid)
    return list(db.session.execute(stmt).scalars().all())
