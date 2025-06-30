import json

from flask import Blueprint, abort, jsonify

from flaskr.models.meal_place import MealPlace
from flaskr.models.models import db
from flaskr.schemas.segment import SimularMealPlaceCacheDTO
from flaskr.services.get_meal_places import get_nearby_cuisins_spots

mod = Blueprint("api/meal_places", __name__, url_prefix="/api/meal_place")


@mod.route("/<int:meal_place_id>/get_simulars")
def get_simulars_meal_places(meal_place_id):
    meal_place = db.session.get(MealPlace, meal_place_id)
    if meal_place is None:
        abort(404)
    simular_meal_places_result = get_nearby_cuisins_spots(
        coords=meal_place.coords,
        cuisine=meal_place.cuisine,
        meal_place_id=meal_place_id,
    )
    if simular_meal_places_result is None:
        return ("", 204)
    return jsonify(
        {
            "simular_meal_places_result": json.dumps(
                [
                    SimularMealPlaceCacheDTO.model_validate(spot).to_dict()
                    for spot in simular_meal_places_result[:4]
                ]
            )
        }
    )
