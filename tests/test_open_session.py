from flask.testing import FlaskClient

from flaskr.models.trip import TripParticipant, TripSession
from flaskr.models.user import User
from flaskr.models.city import City
from flaskr.models.route import Route


def test_block_open_session_page_if_not_joined_and_have_not_uuid(
    multiply_sessions: list[TripSession],
    participants_different_admin_count: list[list[TripParticipant]],
    client: FlaskClient,
):
    """
    Если пользователь впервый раз заходит на сайт и сразу пытается
    попасть в сессию, к которой не присоединен, то отказано в доступе
    """
    resp_setup = client.get(
        "/trip-setup/", query_string={"sessionId": multiply_sessions[0].id}
    )  # переходим по карточке route
    assert resp_setup.status_code == 401  # отказано в доступе

    resp_itinerary = client.get(
        "/trip-itinerary/", query_string={"sessionId": multiply_sessions[0].id}
    )  # переходим по карточке route
    assert resp_itinerary.status_code == 401  # отказано в доступе


def test_open_session_page_if_not_joined(
    add_cities: list[City],
    routes: list[Route],
    users: list[User],
    multiply_sessions: list[TripSession],
    participants_different_admin_count: list[list[TripParticipant]],
    client: FlaskClient,
):
    """
    Если пользователь перешел на страницу поездки, но не присоединен к ней
    """
    with client.session_transaction() as session:
        # устанавливаем uuid пользователя, у которого нет доступа к поездке
        session["uuid"] = users[3].uuid

    resp_setup = client.get(
        "/trip-setup/", query_string={"sessionId": multiply_sessions[0].id}
    )  # переходим по карточке route
    assert resp_setup.status_code == 401  # отказано в доступе

    resp_itinerary = client.get(
        "/trip-itinerary/", query_string={"sessionId": multiply_sessions[0].id}
    )  # переходим по карточке route
    assert resp_itinerary.status_code == 401  # отказано в доступе
