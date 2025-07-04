from typing import List

from sqlalchemy import select
from flaskr.models.models import db
from flaskr.models.cities import City


def get_all_cities() -> List[City]:
    return list(db.session.execute(select(City)).scalars().all())


def get_city(id: int) -> City | None:
    return db.session.get(City, id)


def get_city_by_slug(slug: str) -> City | None:
    stmt = select(City).filter(City.slug == slug)
    return db.session.execute(stmt).scalar()
