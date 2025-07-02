from typing import List
import uuid

from sqlalchemy import select

from flaskr.models.models import db
from flaskr.models.trip import TripParticipant
from flaskr.models.user import Traveler


def get_named_participants(session_id: int) -> List[TripParticipant]:
    criteria = [TripParticipant.session_id == session_id, Traveler.name.isnot(None)]
    stmt = select(TripParticipant).join(TripParticipant.user).filter(*criteria)
    return list(db.session.execute(stmt).scalars().all())


def create_participant(
    user_uuid: uuid.UUID, session_id: int, is_admin: bool = False
) -> TripParticipant:
    participant = TripParticipant(
        user_uuid=user_uuid, session_id=session_id, is_admin=is_admin
    )
    db.session.add(participant)
    db.session.commit()
    return participant
