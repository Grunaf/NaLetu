from uuid import UUID
from flaskr.models.models import db
from flaskr.models.user import Traveler


def create_traveler_db(uuid: UUID) -> Traveler:
    traveler = Traveler(uuid=uuid)

    db.session.add(traveler)
    db.session.commit()
    return traveler


def get_traveler_db(uuid: UUID) -> Traveler | None:
    existing_traveler = db.session.get(Traveler, uuid)
    return existing_traveler
