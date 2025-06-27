from flask.testing import FlaskClient
from flaskr.models.city import City
from tests.conftest import capture_template_rendered
from tests.factories import CityFactory, RouteFactory
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
    RouteFactory.create(
        title="Kazan – Kavkaz", city__lat=55.7944, city__lon=49.1110
    )
    RouteFactory.create(
        title="Sergiev Posad", city__lat=56.3000, city__lon=38.1333
    )
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
