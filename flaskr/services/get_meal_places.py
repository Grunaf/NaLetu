import json
from typing import List

import requests
from flaskr.constants import FIELDS_FOR_MEAL_PLACE
from geopy.distance import geodesic

from flaskr.db.meal_places import get_meal_place_cache_by_id
from config import DGIS_API_KEY, DGIS_API_URI
from flaskr.models.meal_place import MealPlace, SimularMealPlaceCache
from flaskr.models.models import db
from flaskr.models.poi import POI


def get_nearby_cuisins_spots(
    coords: str, cuisine: str, meal_place_id: int
) -> List[SimularMealPlaceCache] | None:
    existed_simular_spots = get_meal_place_cache_by_id(meal_place_id)
    if existed_simular_spots is not None:
        return existed_simular_spots

    replaced_lat_lon = f"{coords.split(',')[1]},{coords.split(',')[0]}"
    responce_meal_places = fetch_from_api_meal_places_near(cuisine, replaced_lat_lon)

    result = get_none_or_result_if_is(responce_meal_places)
    if result is None:
        return None

    simular_meal_places: SimularMealPlaceCache = add_simular_meal_places_in_db(
        meal_place_id=meal_place_id, items_json=result["items"]
    )
    return simular_meal_places


def get_none_or_result_if_is(response):
    if response.status_code != 200:
        data = json.loads(response.text)
        if result := data.get("result") is None:
            return None

        return None

    return result



def fetch_from_api_meal_places_near(cuisine: str, coords: str):
    query = f"поесть {cuisine[:-2]}ую кухню"

    params = {
        "q": query,
        "fields": FIELDS_FOR_MEAL_PLACE,
        "location": coords,
        "locale": "ru_RU",
        "key": DGIS_API_KEY,
    }

    return requests.get(DGIS_API_URI, params)


def add_simular_meal_places_in_db(
    meal_place_id: int, items_json: json
) -> List[SimularMealPlaceCache]:
    simular_spots = []
    for meal_place in items_json:
        simular_spots.append(
            SimularMealPlaceCache(meal_place_id=meal_place_id, data_json=meal_place)
        )
        db.session.add(simular_spots[-1])
    db.session.commit()
    return simular_spots


def get_f_db_meal_places_near_poi(poi: POI) -> List[MealPlace]:
    meal_city_near = []
    radius = 0.4
    checked_cities = []
    while len(meal_city_near) <= 6:
        meal_places_in_city = list(
            MealPlace.query.filter(MealPlace.city_id == poi.segment[0].city_id)
            .filter(MealPlace.id.not_in(checked_cities))
            .limit(6)
            .all()
        )
        if len(meal_places_in_city) == 0:
            break
        checked_cities.extend(m.id for m in meal_places_in_city)
        is_in_radius = (
            lambda coords: geodesic(
                (poi.lat, poi.lon), tuple(coords.split(","))
            ).kilometers
            < radius
        )
        meal_city_near = [m for m in meal_places_in_city if is_in_radius(m.coords)]

    return meal_city_near
