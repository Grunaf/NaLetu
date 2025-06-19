from flask_sqlalchemy import SQLAlchemy
from models.trip import TripParticipant
from flask import session, url_for, request
from conftest import capture_template_rendered

def test_create_session_when_none_exists(add_cities, route, client):
    """
    Если сессий нет, то создается новая
    """
    resp = client.post("/api/session/create_or_get",
                        json={"routeId": route.id, "departureCityId": add_cities[0].id}) # переходим по карточке route
    
    assert resp.status_code == 200
    assert 1 == resp.json["sessionId"] # новая запись в пустой бд

def test_create_session_if_not_admin(add_cities, routes, users, participants_different_admin_count, client):
    """
    Если пользователь находится в группах, но сам не создавал, то создается новая
    """
    with client.session_transaction() as session:
        session["uuid"] = users[1].uuid # устанавливаем uuid пользователя, не являющегося админом
    resp = client.post("/api/session/create_or_get",
                        json={"routeId": routes[2].id, "departureCityId": add_cities[0].id}) # переходим по карточке route
    
    assert resp.status_code == 200
    assert 4 == resp.json["sessionId"] # новая запись в заполненной бд, поэтому 4

def test_get_existing_session_for_admin(add_cities, routes, users, multiply_sessions, participants_different_admin_count, client):   
    """
    Если пользователь админ в разных группах, то получаем существующую
    """
    with client.session_transaction() as session:
        session["uuid"] = users[2].uuid # устанавливаем uuid пользователя, являющегося админом
    resp = client.post("/api/session/create_or_get",
                        json={"routeId": routes[2].id, "departureCityId": add_cities[0].id}) # переходим по карточке route
    
    assert resp.status_code == 200
    assert multiply_sessions[2].id == resp.json["sessionId"] # получаем существующую сессию, с тем же route


def test_join_to_session_if_have_not_uuid(add_cities, routes, users, multiply_sessions, participants_different_admin_count, trip_invites, client):
    """
    Если пользователь не заходил до этого на сайт, и перешел
    по пригласительной ссылки, то добавляем
    """
    with capture_template_rendered(client.application) as template:
        resp = client.get(f"/api/session/join_by_token/{trip_invites[0].uuid}",
                           follow_redirects=True) # переходим по пригласительной ссылке
        
        assert len(resp.history) == 1 # должны перейти на страницу сессии
        assert resp.status_code == 200 # успешно
        assert f"/trip-setup/" in resp.request.path
        assert template[0][1]["plan"]["session_id"] == multiply_sessions[0].id # получили доступ к той сессии, что привазана в приглашении

def test_join_to_session_if_already_joined(add_cities, routes, users, multiply_sessions, participants_different_admin_count, trip_invites, client):
    """
    Если пользователь уже присоединился к сессии, но переходит по ссылке снова,
    то перекидываем на страницу поездки
    """
    with client.session_transaction() as session:
        session["uuid"] = users[2].uuid # устанавливаем uuid пользователя, у которого есть доступ к поездке

    with capture_template_rendered(client.application) as template:
        resp = client.get(f"/api/session/join_by_token/{trip_invites[3].uuid}", follow_redirects=True) # переходим по пригласительной ссылке
        
        assert len(resp.history) == 1 # должны перейти на страницу сессии
        assert resp.status_code == 200 # успешно
        assert f"/trip-setup/" in resp.request.path
        assert template[0][1]["plan"]["session_id"] == multiply_sessions[2].id # получили доступ к той сессии, что привазана в приглашении

def test_create_link_invite(multiply_sessions, client):
    """
    Создание пригласительной ссылки
    """
    print(multiply_sessions[0].uuid)
    resp = client.post(f"/api/session/{multiply_sessions[0].uuid}/create_invite") # создаем пригласительную ссылку

    assert resp.status_code == 200 # успешно
    assert f"/api/session/join_by_token/" in resp.json["link"] # ссылка вернулась

