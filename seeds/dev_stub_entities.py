import os

from flaskr.models.models import db
from flaskr.models.city import City
from flaskr.models.route import Route, RouteCity


def seed_stub_entities():
    if os.getenv("FLASK_ENV") == "prod":
        raise RuntimeError("NEVER seed stub entities in production!")

    # 1. Создаём город (если нет)
    city = City.query.get(1)
    if not city:
        city = City(id=1, name="Stub City")
        db.session.add(city)

    # 2. Создаём маршрут (если нет)
    route = Route.query.get(1)
    if not route:
        route = Route(id=1, title="Stub Route")
        db.session.add(route)

    # 3. Создаём связку route_city
    route_city = RouteCity.query.get(100)
    if not route_city:
        route_city = RouteCity(id=100, route_id=1, city_id=1, order=100)
        db.session.add(route_city)

    db.session.commit()
