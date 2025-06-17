from models.meal_place import SimularMealPlaceCache
import requests, os, json
from models.models import db
from sqlalchemy import select

DGIS_API_KEY = os.getenv("DGIS_API_KEY")
DGIS_API_URI = os.getenv("DGIS_API_URI")
def get_nearby_cuisins_spots(coords: str, cuisine: str, meal_place_id: int) -> list[SimularMealPlaceCache]:
    stmt = select(SimularMealPlaceCache).where(SimularMealPlaceCache.meal_place_id==meal_place_id)
    if existed_simular_spots:= db.session.execute(stmt).scalars().all():
        return existed_simular_spots

    params = {
        "q": f"поесть {cuisine[:-2]}ую кухню",
        "fields": "items.schedule,"
        "items.external_content,"
        "items.reviews,"
        "items.description,"
        "items.attribute_groups",
        "location": f"{coords.split(",")[1]},{coords.split(",")[0]}",
        "locale": "ru_RU",
        "key": DGIS_API_KEY
    }
    responce = requests.get(DGIS_API_URI, params)
    if responce.status_code == 200:
        data = json.loads(responce.text)
        if result:= data.get("result"):
            return add_simular_meal_places_in_db(meal_place_id=meal_place_id, items_json=result["items"])
        else:
            return None
        
def add_simular_meal_places_in_db(meal_place_id: int, items_json: json) -> list[SimularMealPlaceCache]:
    simular_spots = []
    print(db)
    for meal_place in items_json:
        simular_spots.append(SimularMealPlaceCache(meal_place_id=meal_place_id, data_json=meal_place))
        db.session.add(simular_spots[-1])
    db.session.commit()
    return simular_spots

        
