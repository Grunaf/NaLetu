from flask.testing import FlaskClient

from models.models import City
from tests.conftest import capture_template_rendered


def test_catalog_ok(client: FlaskClient, add_cities: list[City]):
    response = client.get("/routes")
    assert response.status_code == 200


def test_catalog_empty_db(client: FlaskClient, add_cities: list[City]):
    with capture_template_rendered(client.application) as templates:
        resp = client.get("/routes")
        assert resp.status_code == 200

        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == "catalog.html"

        assert "routes" in context
        assert isinstance(context["routes"], list)
        assert context["routes"] == []


def test_catalog_multiply_routes_db(client: FlaskClient, sample_routes: None):
    with capture_template_rendered(client.application) as templates:
        resp = client.get("/routes")
        assert resp._status_code == 200
        template, context = templates[0]
        assert len(templates) == 1
        assert template.name == "catalog.html"
        routes = context["routes"]
        routes_title = {r["title"] for r in routes}
        assert len(routes) == 2
        assert routes_title == {"Kazan – Kavkaz", "Sergiev Posad"}


def test_catalog_start_coords(client: FlaskClient, sample_routes: None):
    with capture_template_rendered(client.application) as templates:
        resp = client.get("/routes")
        assert resp.status_code == 200
        assert len(templates) == 1
        template, context = templates[0]
        context_routes = context["routes"]
        assert context_routes[0]["start_coords"] == [55.7944, 49.1110]
        assert context_routes[1]["start_coords"] == [56.3000, 38.1333]
