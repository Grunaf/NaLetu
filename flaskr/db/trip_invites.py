import uuid

from sqlalchemy import select
from flaskr.models.models import db
from flaskr.models.trip import TripInvite


def get_trip_invite_by_uuid(uuid: uuid) -> TripInvite:
    stmt = select(TripInvite).where(TripInvite.uuid == uuid)
    return db.session.execute(stmt).scalars().first()
