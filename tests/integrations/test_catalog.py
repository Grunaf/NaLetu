import random
from flask.testing import FlaskClient
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from flaskr.constants import RADIUS_SEARCH_ROUTES_IN_METERS
from flaskr.models.cities import City
from flaskr.models.models import db
from flaskr.services.routes import get_routes_for_departure_city
from tests.conftest import capture_template_rendered
from tests.factories import CityFactory, RouteFactory, faker
import pytest


@pytest.fixture
def cities() -> list[City]:
    return CityFactory.create_batch(3)


def test_catalog_ok(client: FlaskClient, cities: list[City]):
    response = client.get("/routes")
    assert response.status_code == 200


def test_catalog_empty_db(client: FlaskClient, cities: list[City]):
    with capture_template_rendered(client.application) as templates:
        resp = client.get("/routes")

        assert resp.status_code == 200
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == "catalog.html"

        assert "routes" in context
        assert isinstance(context["routes"], list)
        assert context["routes"] == []


def test_catalog_multiply_routes_db(client: FlaskClient):
    RouteFactory.create(title="Kazan – Kavkaz", city__lat=55.7944, city__lon=49.1110)
    RouteFactory.create(title="Sergiev Posad", city__lat=56.3000, city__lon=38.1333)
    with capture_template_rendered(client.application) as templates:
        resp = client.get("/routes")

        assert resp._status_code == 200
        template, context = templates[0]
        assert len(templates) == 1

        msg_error = "Should be catalog page"
        assert template.name == "catalog.html", msg_error
        routes = context["routes"]
        routes_title = {r["title"] for r in routes}
        msg_error = "Should be two routes"
        assert len(routes) == 2, msg_error

        msg_error = "Should be coords of start city_route"
        assert routes_title == {"Kazan – Kavkaz", "Sergiev Posad"}
        assert routes[0]["start_coords"] == [55.7944, 49.1110], msg_error
        assert routes[1]["start_coords"] == [56.3000, 38.1333], msg_error


def test_get_routes_for_departure_city_no_routes():
    pass


@pytest.mark.parametrize(
    "start_city_coord, count_finded_route",
    [
        [(55.671087, 45.848852), 0],  # 205 km
        [(55.806895, 50.846017), 1],  # 110 km
        [(55.81378, 49.093038), 1],  # 120 km Чебоксары
        [(54.171895, 50.4682), 0],  # 200.1 km
    ],
)
def test_get_routes_for_departure_city_not_near(start_city_coord, count_finded_route):
    departure_lat, departure_lon = (55.7944, 49.111)
    departure_city = CityFactory.create(lat=departure_lat, lon=departure_lon)
    RouteFactory.create_batch(2)
    route = RouteFactory.create(
        cities=2,
    )
    start_city = db.session.merge(route.start_city.city)
    start_city.lat, start_city.lon = start_city_coord
    start_city.location = from_shape(Point(start_city.lon, start_city.lat), srid=4326)
    db.session.commit()

    get_routes = get_routes_for_departure_city(
        departure_city.location, departure_city.lat
    )

    assert len(get_routes) == count_finded_route
