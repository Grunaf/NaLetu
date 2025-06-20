from models.trip import TripVote, User, TripParticipant, TripSession
from models.models import DayVariant
from flask.testing import FlaskClient

def test_vote_if_is_participant(users, participants_different_admin_count: list[list[TripParticipant]],
                                 variants: list[list[DayVariant]], multiply_sessions: list[TripSession], client: FlaskClient):
    """
    Если пользователь проголосует в поездке,
    к которой имеет доступ, то успешно (200)
    """
    with client.session_transaction() as session:
        session["uuid"] = users[0].uuid

    choices = [
        {variants[0][0].id: variants[0][0].day.day_order},
        {variants[1][0].id: variants[1][0].day.day_order},
        {variants[2][1].id: variants[2][1].day.day_order},
    ]
    resp = client.post("/api/session/vote",
                        json={"choices": choices, "session_id": multiply_sessions[0].id})
    
    assert resp.status_code == 200 # Успешно
    expected_votes = [
        {
            "session_id": multiply_sessions[0].id, "variant_id": variants[0][0].id,
            "participant_id": participants_different_admin_count[0][0].id,
            "day_order": variants[0][0].day.day_order
        },
        {
            "session_id": multiply_sessions[0].id, "variant_id": variants[1][0].id,
            "participant_id": participants_different_admin_count[0][0].id,
            "day_order": variants[1][0].day.day_order
        },
        {
            "session_id": multiply_sessions[0].id, "variant_id": variants[2][1].id,
            "participant_id": participants_different_admin_count[0][0].id,
            "day_order": variants[2][1].day.day_order
        }]
    
    for expected_vote, returned_vote in zip(expected_votes, resp.json["votes"]):
        assert expected_vote == returned_vote

def test_vote_if_is_not_participant(users, participants_different_admin_count: list[list[TripParticipant]],
                                 variants: list[list[DayVariant]], multiply_sessions: list[TripSession], client: FlaskClient):
    """
    Если пользователь проголосует в поездке,
    к которой не имеет доступа, то отказано в доступе (403)
    """
    with client.session_transaction() as session:
        session["uuid"] = users[0].uuid

    choices = [
        {variants[0][0].id: variants[0][0].day.day_order},
        {variants[1][0].id: variants[1][0].day.day_order},
        {variants[2][1].id: variants[2][1].day.day_order},
    ]
    resp = client.post("/api/session/vote",
                        json={"choices": choices, "session_id": multiply_sessions[2].id})
    
    assert resp.status_code == 403 # отказано в доступе

# def test_change_votes(users, participants_different_admin_count: list[list[TripParticipant]],
#                                  variants: list[list[DayVariant]], multiply_sessions: list[TripSession], client: FlaskClient)

def test_vote_when_voting_is_finished(users, participant_votes, variants: list[list[DayVariant]],
                                       session, client: FlaskClient):
    """
    Если пользователь проголосует, когда голосование завершилось, то отказано (422)
    """
    with client.session_transaction() as fk_session:
        fk_session["uuid"] = users[0].uuid

    choices = [
        {variants[0][0].id: variants[0][0].day.day_order},
        {variants[1][0].id: variants[1][0].day.day_order},
        {variants[2][1].id: variants[2][1].day.day_order},
    ]
    resp = client.post("/api/session/vote",
                        json={"choices": choices, "session_id": session.id})
    
    assert resp.status_code == 422 # голосование завершилось
