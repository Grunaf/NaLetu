from models.meal_place import SimularMealPlaceCache
from services.get_meal_places import get_f_db_meal_places_near_poi
from services.get_f_api_meal_places import get_nearby_cuisins_spots
from conftest import mock_2gis_request

def test_get_simular_spots(meal_places, mocker):
    mock_2gis_request(mocker, '{"result": {"items":[{"address_name": "Камуршинова 45в"},' \
                        '{"address_name": "Легитова 12в"},' \
                        '{"address_name": "Абелинская 2Ж"}]}}')
    nearby_spots = get_nearby_cuisins_spots(meal_places[0].coords, 
                                            meal_places[0].cuisine,
                                            meal_places[0].id)
    
    expected_spots = {(meal_places[0].id, "Камуршинова 45в"),
                        (meal_places[0].id, "Легитова 12в"),
                        (meal_places[0].id, "Абелинская 2Ж")}
    
    pair_nearby_spots = {(ns.meal_place_id, ns.data_json["address_name"]) for ns in nearby_spots}
    assert pair_nearby_spots == expected_spots

def test_get_simular_spots_empty_result(meal_places, mocker):
    mock_2gis_request(mocker, '{"meta":{"error":{"message":"Results not found","type":"itemNotFound"}}}')

    nearby_spots = get_nearby_cuisins_spots(meal_places[0].coords, 
                                            meal_places[0].cuisine,
                                            meal_places[0].id)
    
    assert nearby_spots is None

def test_get_simular_spots_mupltiply_items(meal_places, mocker):
    mock_2gis_request(mocker, '{"result": {"items":[{"address_name": "Камуршинова 45в"}]}}')
    
    nearby_spots = get_nearby_cuisins_spots(meal_places[0].coords, 
                                            meal_places[0].cuisine,
                                            meal_places[0].id)
    
    expected_spots = (meal_places[0].id, {"address_name": "Камуршинова 45в"})

    assert len(nearby_spots) == 1
    assert (nearby_spots[0].meal_place_id, nearby_spots[0].data_json) == expected_spots

def test_api_get_simular_spots(client, meal_places):
    resp = client.get(f"/api/meal_place/{meal_places[0].id}/get_simulars")
    assert resp.status_code == 200
    assert "simular_meal_places_result" in resp.json


def test_get_meal_places(poi, meal_places):
    mps_near = get_f_db_meal_places_near_poi(poi)
    assert len(mps_near) == 3
    for mp in meal_places:
        assert mp in mps_near
