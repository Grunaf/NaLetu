import uuid

from flask import session as fk_session
from flaskr.db.travelers import create_traveler_db, get_traveler
from flaskr.models.user import Traveler


def get_uuid_traveler() -> uuid.UUID:
    raw_uuid = fk_session.get("uuid")
    return uuid.UUID(raw_uuid)


def get_or_create_traveler(uuid: uuid.UUID, name: str | None = None) -> Traveler:
    existing_traveler = get_traveler(uuid)
    if existing_traveler is not None:
        return existing_traveler
    return create_traveler_db(uuid, name)


def is_traveler_in_session(traveler_uuid: uuid.UUID, session_uuid: uuid.UUID) -> bool:
    user = get_traveler(traveler_uuid)
    if user is None:
        return False

    return any(
        participation.session.uuid == session_uuid
        for participation in user.participations
    )
