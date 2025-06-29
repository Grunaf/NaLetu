from flask.testing import FlaskClient

from tests.conftest import mock_2gis_request
from flaskr.models.meal_place import MealPlace
from flaskr.models.route import POI
from flaskr.services.get_meal_places import get_f_db_meal_places_near_poi
from flaskr.services.get_meal_places import get_nearby_cuisins_spots
from tests.factories import MealPlaceFactory, POIFactory
import pytest


@pytest.fixture
def meal_place() -> MealPlace:
    return MealPlaceFactory.build()


def test_get_simular_spots(meal_place: MealPlace, mocker):
    mock_2gis_request(
        mocker,
        '{"result": {"items":[{"address_name": "Камуршинова 45в"},'
        '{"address_name": "Легитова 12в"},'
        '{"address_name": "Абелинская 2Ж"}]}}',
    )
    nearby_spots = get_nearby_cuisins_spots(
        meal_place.coords, meal_place.cuisine, meal_place.id
    )

    expected_spots = {
        (meal_place.id, "Камуршинова 45в"),
        (meal_place.id, "Легитова 12в"),
        (meal_place.id, "Абелинская 2Ж"),
    }

    msg_error = "Addresses should equal"
    pair_nearby_spots = {
        (spot.meal_place_id, spot.data_json["address_name"]) for spot in nearby_spots
    }
    assert pair_nearby_spots == expected_spots, msg_error


def test_get_simular_spots_empty_result(meal_place: MealPlace, mocker):
    mock_2gis_request(
        mocker,
        '{"meta":{"error":{"message":"Results not found","type":"itemNotFound"}}}',
    )

    nearby_spots = get_nearby_cuisins_spots(
        meal_place.coords, meal_place.cuisine, meal_place.id
    )

    assert nearby_spots is None


def test_get_simular_spots_mupltiply_items(meal_place, mocker):
    mock_2gis_request(
        mocker, '{"result": {"items":[{"address_name": "Камуршинова 45в"}]}}'
    )

    nearby_spots = get_nearby_cuisins_spots(
        meal_place.coords, meal_place.cuisine, meal_place.id
    )

    expected_spots = (meal_place.id, {"address_name": "Камуршинова 45в"})

    assert len(nearby_spots) == 1
    assert (
        nearby_spots[0].meal_place_id,
        nearby_spots[0].data_json,
    ) == expected_spots


def test_api_get_simular_spots(meal_place: MealPlace, client: FlaskClient):
    resp = client.get(f"/api/meal_place/{meal_place.id}/get_simulars")
    assert resp.status_code == 200
    assert "simular_meal_places_result" in resp.json


def test_get_meal_places():
    poi = POIFactory.create(lat=59.91433, lon=30.29920)

    MealPlaceFactory.create_batch(10)
    meal_places = [
        MealPlaceFactory.create(coords="59.91506,30.29443"),  # 350 m
        MealPlaceFactory.create(coords="59.913384,30.303769"),  # 250 m
        MealPlaceFactory.create(coords="59.908071,30.29676"),  # 700 m
        MealPlaceFactory.create(coords="59.91973,30.306001"),  # 800 m
        MealPlaceFactory.create(coords="59.9105,30.319219")  # 1.2 km
    ]
    
    mps_near = get_f_db_meal_places_near_poi(poi)
    assert len(mps_near) == 2
    for mp in meal_places:
        assert mp in mps_near
