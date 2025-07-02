from typing import List
import uuid

from sqlalchemy import select
from flaskr.models.models import db
from flaskr.models.trip import TripVote


def get_session_votes_for_variant_id(
    variant_id: int, session_id: int
) -> List[TripVote]:
    stmt = (
        select(TripVote)
        .filter(TripVote.variant_id == variant_id)
        .filter(TripVote.session_id == session_id)
    )
    return list(db.session.execute(stmt).scalars())


def get_trip_votes_by_uuid(session_id: uuid) -> List[TripVote]:
    stmt = select(TripVote).where(TripVote.session_id == session_id)
    return db.session.execute(stmt).scalars().all()
