from flask.testing import FlaskClient

from flaskr.models.city import City
from flaskr.models.user import User
from flaskr.models.route import Day, DayVariant, Route
from flaskr.models.trip import TripParticipant, TripSession, TripVote
from flaskr.schemas.route import DayRead
from flaskr.services.voting import get_days_with_winner_variant


def test_status_code_itinerary_page(
    add_cities: list[City],
    routes: list[Route],
    users: list[User],
    multiply_sessions: list[TripSession],
    participants_different_admin_count: list[list[TripParticipant]],
    client: FlaskClient,
):
    """
    Если пользователь перешел на страницу деталей поездки,
    к которой он присоединен, то открываем страницу
    """
    with client.session_transaction() as session:
        # устанавливаем uuid пользователя, у которого есть доступ к поездке
        session["uuid"] = users[2].uuid

    resp = client.get(
        "/trip-itinerary/", query_string={"sessionId": multiply_sessions[2].id}
    )  # переходим к маршруту поездки

    assert resp.status_code == 200  # успешно


def test_trip_itinerary_bad_request(
    add_cities: list[City],
    routes: list,
    users: list[User],
    multiply_sessions: list[TripSession],
    participant_votes: list[list[TripVote]],
    participants_different_admin_count: list[list[TripParticipant]],
    client: FlaskClient,
):
    """
    Если не указан id сессии, то возвращаем 400
    """
    with client.session_transaction() as session:
        # устанавливаем uuid пользователя, у которого есть доступ к поездке
        session["uuid"] = users[2].uuid

    resp = client.get("/trip-itinerary/")  # не указываем id сессии
    assert resp.status_code == 400


def test_open_itinerary_if_not_existing_entry(
    add_cities: list[City],
    routes: list,
    users: list[User],
    multiply_sessions: list[TripSession],
    participant_votes: list[list[TripVote]],
    participants_different_admin_count: list[list[TripParticipant]],
    client: FlaskClient,
):
    """
    Если указан id не существующей сессии, то вернется 401,
    так как в личном списке нет запрашиваемой сессии,
    то есть отказано в доступе
    """
    with client.session_transaction() as session:
        # устанавливаем uuid пользователя, у которого есть доступ к поездке
        session["uuid"] = users[2].uuid

    resp = client.get(
        "/trip-itinerary/", query_string={"sessionId": 10}
    )  # указываем id которого нет
    assert resp.status_code == 401


def test_get_days_with_winner_variant(
    route: Route,
    days: list[Day],
    variants: list[list[DayVariant]],
    participant_votes: list[list[TripVote]],
    client: FlaskClient,
):
    """
    Если варианты за которые проголосовали не соответсвуют результату функции
    """
    # ожидамый результат
    expected_winners = [
        DayRead(id=days[0].id, day_order=days[0].day_order, variant=variants[0][1]),
        DayRead(id=days[1].id, day_order=days[1].day_order, variant=variants[1][1]),
        DayRead(id=days[2].id, day_order=days[2].day_order, variant=variants[2][1]),
    ]

    # вызов функции с указанием списка голосов и количества дней
    func_winners = get_days_with_winner_variant(
        [*participant_votes[0], *participant_votes[1], *participant_votes[2]],
        route.duration_days,
    )

    for expected, result in zip(expected_winners, func_winners):
        assert expected == result
