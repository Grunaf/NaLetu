from flask_sqlalchemy import SQLAlchemy
from models.trip import TripParticipant
from flask import session

def test_create_or_get_session_no_sessions(add_cities, route, client):
    resp = client.post("/api/session/create_or_get",
                        json={"routeId": route.id, "departureCityId": add_cities[0].id})
    
    assert resp.status_code == 200
    assert 1 == resp.json["sessionId"] # new session

def test_create_or_get_session_multiply_sessions_where_participant_not_user(add_cities, route, users, participants_different_admin_count, client):
    session["uuid"] = users[1].uuid
    resp = client.post("/api/session/create_or_get",
                        json={"routeId": route.id, "departureCityId": add_cities[0].id})
    
    assert resp.status_code == 200
    assert 4 == resp.json["sessionId"] # new session

def test_create_or_get_session_multiply_sessions_where_participant_admin_in_two_session(add_cities, route, users, participants_different_admin_count, client):
    session["uuid"] = users[0].uuid
    resp = client.post("/api/session/create_or_get",
                        json={"routeId": route.id, "departureCityId": add_cities[0].id})
    
    assert resp.status_code == 200
    assert 1 == resp.json["sessionId"] # new session
