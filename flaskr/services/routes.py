from typing import List
from geoalchemy2 import WKBElement
from sqlalchemy import select

from flaskr.constants import RADIUS_SEARCH_ROUTES_IN_METERS
from flaskr.models.models import db
from flaskr.models.cities import City
from geoalchemy2.functions import ST_DWithin

from flaskr.models.route import Route, RouteCity
from flaskr.utils import meters_to_degrees


def get_routes_for_departure_city(city_loc: WKBElement, city_lat: float) -> List[Route]:
    deg_lat, _ = meters_to_degrees(RADIUS_SEARCH_ROUTES_IN_METERS, city_lat)
    stmt = select(City).filter(
        ST_DWithin(
            City.location,
            city_loc,
            deg_lat,
        )
    )
    cities = list(db.session.execute(stmt).scalars().all())
    print(cities)
    cities_id = [city.id for city in cities]

    stmt = (
        select(RouteCity)
        .filter(RouteCity.city_id.in_(cities_id), RouteCity.order == 1)
        .order_by(RouteCity.city_id)
    )
    route_cities = db.session.execute(stmt).scalars().all()

    return [route_city.route for route_city in route_cities]
