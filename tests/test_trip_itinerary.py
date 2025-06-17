from tests.conftest import capture_template_rendered
from flaskr import get_winners_day_variants


def test_trip_itinerary_status_code(client, detailed_session, participant_votes):
    with capture_template_rendered(client.application) as templates:
        resp = client.get("trip-itinerary", query_string={"sessionId": 1})
        assert resp.status_code == 200
    assert len(templates) == 1
    template, context = templates[0]
    assert template.name == "trip-itinerary.html"
    for key in ("route", "session", "days", "transports", "ya_map_js_api_key"):
        assert key in context

def test_trip_titnerary_bad_request(client):
    with capture_template_rendered(client.application) as templates:
        resp = client.get("trip-itinerary")
        assert resp.status_code == 400

def test_trip_titnerary_empty_db(client):
    with capture_template_rendered(client.application) as templates:
        resp = client.get("trip-itinerary", query_string={"sessionId": 1})
        assert resp.status_code == 404
    
def test_trip_itinerary_winner_variants(client, participant_votes):
    with capture_template_rendered(client.application) as templates:
        resp = client.get("trip-itinerary", query_string={"sessionId": 1})
        assert resp.status_code == 200
    assert len(templates) == 1
    template, context = templates[0]
    assert template.name == "trip-itinerary.html"
    winner_variants = get_winners_day_variants(votes=[*participant_votes[0], *participant_votes[1], *participant_votes[2]], day_count=len(participant_votes[0]))
    for win_var, day in zip(winner_variants, context["days"]):
        assert win_var.id == day["variant_id"]