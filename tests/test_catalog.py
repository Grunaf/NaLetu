from tests.conftest import capture_template_rendered, contextmanager
from models import Route, RouteCity


# Status code and template rendering: send a GET request to /routes and assert that the response status is 200 and that it uses the catalog.html template.
def test_catalog_ok(client):
    response = client.get('/routes')
    assert response.status_code == 200

# Empty database scenario: clear all Route records, request /routes, and verify the routes context variable is an empty list.
def test_catalog_empty_db(client):
    with capture_template_rendered(client.application) as templates:
        resp = client.get("/routes")
        assert resp.status_code == 200

        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == "catalog.html"

        assert "routes" in context
        assert isinstance(context["routes"], list)
        assert context["routes"] == []

# Multiple routes: add two or more distinct Route entries (each with their own cities and POIs), request /routes, and check that the routes list contains exactly two items and that each item’s fields correspond to the correct Route record.
def test_catalog_multiply_routes_db(client, sample_routes):
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

# Start coordinates logic: for a Route where the first City has specific lat/lon, confirm that start_coords in the response matches [lat, lon] of that first city.
def test_catalog_start_coords(client, sample_routes):
    with capture_template_rendered(client.application) as templates:
        resp = client.get("/routes")
        assert resp.status_code == 200
        assert len(templates) == 1
        template, context = templates[0]
        context_routes = context["routes"]
        assert context_routes[0]["start_coords"] == [55.7944, 49.1110] 
        assert context_routes[1]["start_coords"] == [56.3000, 38.1333] 


