from tests.conftest import capture_template_rendered
from models import Route

def test_trip_setup_status_code(client, sample_session):
    resp = client.get("/trip-setup", query_string={"sessionId" : "e388f4df-8b44-4f92-833d-127b16c3ae4a"})
    assert resp.status_code == 200

def test_trip_setup_not_existing_entry(client):
    resp = client.get("/trip-setup", query_string={"sessionId": "e388f4df-8b44-4f92-833d-127b16c3ae4a"})
    assert resp.status_code == 404

def test_trip_setup_mupltiply_entries_db(client, sample_routes):
    with capture_template_rendered(client.application) as templates:
        resp = client.get("/trip-setup", query_string={"sessionId": "e388f4df-8b44-4f92-833d-127b16c3ae4a"})
        assert resp.status_code == 200
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == "trip-setup.html"
        assert "plan" in context
        plan = context["plan"]
        assert plan["session_id"] == "e388f4df-8b44-4f92-833d-127b16c3ae4a"
    
    