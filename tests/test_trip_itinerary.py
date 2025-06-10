from tests.conftest import capture_template_rendered, contextmanager

def test_trip_titnerary_status_code(client, full_route):
    with capture_template_rendered(client.application) as templates:
        resp = client.get("trip-itinerary", query_string={"sessionId": "s1"})
        assert resp.status_code == 200
    assert len(templates) == 1
    template, context = templates[0]
    assert template.name == "trip-itinerary.html"
    for key in ("route", "session", "days", "transports"):
        assert key in context