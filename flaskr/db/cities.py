from typing import List

from sqlalchemy import select
from flaskr.models.models import db
from flaskr.models.city import City


def get_all_cities() -> List[City]:
    stmt = select(City)
    return list(db.session.execute(stmt).scalars().all())
