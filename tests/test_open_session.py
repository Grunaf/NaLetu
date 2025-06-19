from tests.conftest import capture_template_rendered
from models.models import Route


def test_block_open_session_page_if_not_joined_and_have_not_uuid(multiply_sessions, participants_different_admin_count, client):   
    """
    Если пользователь впервый раз заходит на сайт и сразу пытается
    попасть в сессию, к которой не присоединен, то отказано в доступе
    """
    resp_setup = client.get("/trip-setup/", query_string={"sessionId": multiply_sessions[0].id}) # переходим по карточке route
    assert resp_setup.status_code == 401 # отказано в доступе
    
    resp_itinerary = client.get("/trip-itinerary/", query_string={"sessionId": multiply_sessions[0].id}) # переходим по карточке route
    assert resp_itinerary.status_code == 401 # отказано в доступе


def test_open_session_page_if_not_joined(add_cities, routes, users, multiply_sessions, participants_different_admin_count, client):   
    """
    Если пользователь перешел на страницу поездки, но не присоединен к ней
    """
    with client.session_transaction() as session:
        session["uuid"] = users[3].uuid # устанавливаем uuid пользователя, у которого нет доступа к поездке

    resp_setup = client.get("/trip-setup/", query_string={"sessionId": multiply_sessions[0].id}) # переходим по карточке route
    assert resp_setup.status_code == 401 # отказано в доступе
    
    resp_itinerary = client.get("/trip-itinerary/", query_string={"sessionId": multiply_sessions[0].id}) # переходим по карточке route
    assert resp_itinerary.status_code == 401 # отказано в доступе

    
    