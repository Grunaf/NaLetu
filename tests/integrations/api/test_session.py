import pytest
from flask.testing import FlaskClient

from flaskr.routes.constants import API_SESSION_URI
from tests.factories import CityFactory, RouteFactory, TravelerFactory


@pytest.mark.parametrize(
    "json_payload, expected_code",
    [
        [None, 400],
        [{}, 400],
        [{"departureCityId": 1}, 400],
        [{"routeId": 1}, 400],
        [
            {"routeId": 1, "departureCityId": 1},
            201,
        ],
    ],
)
def test_create_session(client: FlaskClient, json_payload, expected_code):
    """
    Если сессий нет, то создается новая
    """
    traveler = TravelerFactory.create()
    route = RouteFactory.create()
    city = CityFactory.create()

    if json_payload is not None:
        if "routeId" in json_payload and json_payload.get("routeId") == 1:
            json_payload["routeId"] = route.id
        if (
            "departureCityId" in json_payload
            and json_payload.get("departureCityId") == 1
        ):
            json_payload["departureCityId"] = city.id

    with client.session_transaction() as session:
        session["uuid"] = str(traveler.uuid)

    resp = client.post(
        API_SESSION_URI, json=json_payload, content_type="application/json"
    )
    assert resp.status_code == expected_code
