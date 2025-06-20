from flask.testing import FlaskClient
from models.models import City, Route
from models.trip import TripParticipant, TripSession, User


def test_status_code_voting_page(
    add_cities: list[City],
    routes: list[Route],
    users: list[User],
    multiply_sessions: list[TripSession],
    participants_different_admin_count: list[list[TripParticipant]],
    client: FlaskClient,
):
    """
    Если пользователь перешел на страницу голосования,
    к которой он присоединен, то открываем страницу
    """
    with client.session_transaction() as session:
        # устанавливаем uuid пользователя, у которого есть доступ к поездке
        session["uuid"] = users[2].uuid

    resp = client.get(
        "/trip-setup/", query_string={"sessionId": multiply_sessions[2].id}
    )  # переходим по карточке route

    assert resp.status_code == 200  # успешно
