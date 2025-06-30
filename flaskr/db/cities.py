from typing import List

from sqlalchemy import select
from flaskr.models.models import db
from flaskr.models.city import City


def get_all_cities() -> List[City]:
    return list(db.session.execute(select(City)).scalars().all())


def get_city(id: int) -> City | None:
    return db.session.get(City, id)
