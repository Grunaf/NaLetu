import json
from typing import List

import requests
from flaskr.constants import FIELDS_FOR_MEAL_PLACE
from geopy.distance import geodesic

from flaskr.db.meal_places import get_meal_place_cache_by_id
from config import DGIS_API_KEY, DGIS_API_URI_ITEMS
from flaskr.db.segments import get_segment_by_poi
from flaskr.models.meal_place import MealPlace, SimularMealPlaceCache
from flaskr.models.models import db
from flaskr.models.route import POI
from flaskr.models.constants import CUISINE

dgis_params = {
    "fields": FIELDS_FOR_MEAL_PLACE,
    "sort": "distance",
    "locale": "ru_RU",
    "key": DGIS_API_KEY,
}


def get_nearby_cuisins_spots(
    coords: str, cuisine: int, meal_place_id: int
) -> List[SimularMealPlaceCache] | None:
    existed_simular_spots = get_meal_place_cache_by_id(meal_place_id)
    if existed_simular_spots is not None:
        return existed_simular_spots

    replaced_lat_lon = f"{coords.split(',')[1]},{coords.split(',')[0]}"
    responce_meal_places = fetch_from_api_cuisine_meal_places(
        cuisine, replaced_lat_lon
    )

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


def fetch_from_api_meal_places(coords: str):
    query = "поесть"
    radius = 1000

    params = {"q": query, "location": coords, "radius": radius, **dgis_params}

    return requests.get(DGIS_API_URI_ITEMS, params)


def fetch_from_api_cuisine_meal_places(cuisine: int, coords: str):
    cuisine_root = CUISINE[cuisine][:-2]
    query = f"поесть {cuisine_root}ую кухню"

    params = {"q": query, "location": coords, **dgis_params}

    return requests.get(DGIS_API_URI_ITEMS, params)


def add_simular_meal_places_in_db(
    meal_place_id: int, items_json: json
) -> List[SimularMealPlaceCache]:
    simular_spots = []
    for meal_place in items_json:
        simular_spots.append(
            SimularMealPlaceCache(
                meal_place_id=meal_place_id, data_json=meal_place
            )
        )
        db.session.add(simular_spots[-1])
    db.session.commit()
    return simular_spots


def is_in_radius(poi1: tuple, poi2: tuple, radius) -> bool:
    distance = geodesic((poi1[0], poi1[1]), tuple(poi2[0], poi2[1]))
    return distance.kilometers < radius


def get_f_db_meal_places_near_poi(
    poi: POI, radius: float = 0.4
) -> List[MealPlace | None]:
    meal_city_near = []
    checked_cities = []
    while len(meal_city_near) <= 6:
        # poi_segment = get_segment_by_poi(poi.id)
        # if poi_segment is None:
        #     return []

        # meal_places_in_city = list(
        #     MealPlace.query.filter(MealPlace.city_id == poi_segment.city_id)
        #     .filter(MealPlace.id.not_in(checked_cities))
        #     .limit(6)
        #     .all()
        # )

        responce_meal_places = fetch_from_api_meal_places(
            poi.get_coords, radius
        )
        result = get_none_or_result_if_is(responce_meal_places)
        if result is None:
            return None

        if len(meal_places_in_city) == 0:
            break
        checked_cities.extend(
            meal_spot.id for meal_spot in meal_places_in_city
        )
        is_in_radius = ()
        meal_city_near = [
            meal_spot
            for meal_spot in meal_places_in_city
            if is_in_radius(
                poi.get_coords, meal_spot.coords.split(","), radius
            )
        ]

    return meal_city_near
