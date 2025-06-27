from typing import List

from sqlalchemy import select

from flaskr.models.models import db
from flaskr.models.trip import TripParticipant


def get_participants_by_session_id(session_id: int) -> List[TripParticipant]:
    stmt = select(TripParticipant).where(
        TripParticipant.session_id == session_id
    )
    return db.session.execute(stmt).scalars().all()
