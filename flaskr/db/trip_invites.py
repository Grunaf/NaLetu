import uuid

from sqlalchemy import select
from flaskr.models.models import db
from flaskr.models.trip import TripInvite


def create_trip_invite(session_uuid: uuid.UUID) -> TripInvite:
    invite = TripInvite(session_uuid=session_uuid)
    db.session.add(invite)
    db.session.commit()
    return invite


def deactivate_trip_invite(invite: TripInvite):
    invite.is_active = False
    db.session.commit()


def get_trip_invite_by_uuid(uuid: uuid.UUID) -> TripInvite | None:
    stmt = select(TripInvite).where(TripInvite.uuid == uuid)
    return db.session.execute(stmt).scalars().first()
