from typing import List

from sqlalchemy import select

from flaskr.models.meal_place import SimularMealPlaceCache
from flaskr.models.models import db


def get_meal_place_cache_by_id(
    meal_place_id: int,
) -> List[SimularMealPlaceCache] | None:
    stmt = select(SimularMealPlaceCache).where(
        SimularMealPlaceCache.meal_place_id == meal_place_id
    )
    existed_simular_spots = db.session.execute(stmt).scalars().all()
    return existed_simular_spots
