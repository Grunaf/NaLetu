from models.models import db, POI
from models.meal_place import MealPlace
from geopy.distance import geodesic 

def get_f_db_meal_places_near_poi(poi: POI) -> list[MealPlace]:
    meal_city_near = []
    radius = 0.4
    checked_cities = []
    while len(meal_city_near) <= 6:
        
        meal_places_in_city = list(MealPlace.query.filter(MealPlace.city_id==poi.segment[0].city_id)
                                   .filter(MealPlace.id.not_in(checked_cities)).limit(6).all())
        if len(meal_places_in_city) == 0:
            break
        checked_cities.extend(m.id for m in meal_places_in_city)
        is_in_radius = lambda coords: geodesic((poi.lat, poi.lon), tuple(coords.split(","))).kilometers < radius
        meal_city_near = [m for m in meal_places_in_city if is_in_radius(m.coords)]
        
    return meal_city_near