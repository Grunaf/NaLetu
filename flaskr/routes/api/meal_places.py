import re
from typing import List

from flask import Blueprint, abort, render_template, request

from flaskr.models.meal_place import MealPlace, SimularMealPlaceCache
from flaskr.models.models import db
from flaskr.schemas.segment import SimularMealPlaceCacheDTO
from flaskr.services.get_meal_places import get_nearby_cuisins_spots

mod = Blueprint("api/meal_places", __name__, url_prefix="/api/meal_place")


def parse_meal_place_json(nearby_similar_meal_places: List[SimularMealPlaceCache]):
    similar_places = []
    for place in nearby_similar_meal_places:
        data = place.data_json

        attribute_avg_price = data["attribute_groups"][0]["attributes"][0]["name"]
        match_price = re.search(r"\d+", attribute_avg_price)

        attribute_avg_price = int(match_price.group()) if match_price else 0
        img_src = ""
        if len(data["external_content"]) != 0:
            img_src = data["external_content"][0]["main_photo_url"]

        name = data["name"]
        address_name = data["address_name"]

        reviews = data["reviews"]
        general_rating = reviews.get("general_rating", 0)
        general_review_count = reviews.get("general_review_count", 0)

        similar_places.append(
            SimularMealPlaceCacheDTO(
                id=place.id,
                meal_place_id=place.meal_place_id,
                name=name,
                general_rating=general_rating,
                general_review_count=general_review_count,
                avg_price=attribute_avg_price,
                img_src=img_src,
                address_name=address_name,
            )
        )
    return similar_places


@mod.route("/<int:meal_place_id>/get_simulars")
def get_simulars_meal_places_for_segment(meal_place_id: int):
    day_order = request.args.get("day-order")
    meal_type = request.args.get("meal-type")
    name_input = f"meal_place_{day_order}_{meal_type}"
    meal_place = db.session.get(MealPlace, meal_place_id)

    if meal_place is None:
        abort(404)

    nearby_similar_meal_places: List[SimularMealPlaceCache] | None = (
        get_nearby_cuisins_spots(
            coords=meal_place.coords,
            cuisine=meal_place.cuisine,
            meal_place_id=meal_place_id,
        )
    )
    if nearby_similar_meal_places is None:
        return ("", 204)

    similar_meal_places_read = parse_meal_place_json(nearby_similar_meal_places)
    return render_template(
        "partials/similar-meal-place.html",
        meal_place_name=meal_place.name,
        name_input=name_input,
        similar_meal_places_read=similar_meal_places_read,
    )
