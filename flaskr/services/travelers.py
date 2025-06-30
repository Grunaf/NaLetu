import uuid

from flask import session as fk_session
from flaskr.db.travelers import create_traveler_db, get_traveler_db
from flaskr.models.user import Traveler


def get_uuid_traveler() -> uuid.UUID:
    raw_uuid = fk_session.get("uuid")
    return uuid.UUID(raw_uuid)


def get_or_create_traveler(uuid: uuid.UUID) -> Traveler:
    existing_traveler = get_traveler_db(uuid)
    if existing_traveler is not None:
        return existing_traveler

    return create_traveler_db(uuid)
