from tests.conftest import capture_template_rendered
from flaskr import get_winners_day_variants
from services.session_utils import get_winners_day_variants


# def test_open_itinerary_page_if_joined(add_cities, routes, users, multiply_sessions, participants_different_admin_count, client):   
#     """
#     Если пользователь перешел на страницу деталей поездки, к которой он присоединен,
#     то открываем страницу
#     """
#     with client.session_transaction() as session:
#         session["uuid"] = users[2].uuid # устанавливаем uuid пользователя, у которого есть доступ к поездке

#     resp = client.get("/trip-ininerary/", query_string={"sessionId": multiply_sessions[2].id}) # переходим по карточке route
    
#     assert resp.status_code == 200 # успешно
    
    

def test_trip_itinerary_bad_request(add_cities, routes, users, multiply_sessions, participant_votes, participants_different_admin_count, client):
    """
    Если не указан id сессии, то возвращаем 400
    """
    with client.session_transaction() as session:
        session["uuid"] = users[2].uuid # устанавливаем uuid пользователя, у которого есть доступ к поездке

    resp = client.get("/trip-itinerary/") # не указываем id сессии
    assert resp.status_code == 400

def test_open_itinerary_if_not_existing_entry(add_cities, routes, users, multiply_sessions, participant_votes, participants_different_admin_count, client):
    """
    Если указан id не существующей сессии, то возвращаем 404
    """
    with client.session_transaction() as session:
        session["uuid"] = users[2].uuid # устанавливаем uuid пользователя, у которого есть доступ к поездке

    resp = client.get("/trip-itinerary/", query_string={"sessionId": 10}) # указываем id которого нет
    assert resp.status_code == 404
    
def test_get_winner_variants(route, variants, participant_votes, client):
    """
    Если варианты за которые проголосовали не соответсвуют с результатом функции
    """
    expected_winners = [variants[0][1], variants[1][1], variants[2][1]] # ожидамый результат
    func_winners = get_winners_day_variants([*participant_votes[0],*participant_votes[1], *participant_votes[2]],
                                             route.duration_days) # вызов функции с указанием списка голосов и количества дней
    
    for expected, result in zip(expected_winners, func_winners):
        assert expected == result

    # assert len(templates) == 1
    # template, context = templates[0]
    # assert template.name == "trip-itinerary.html"
    # winner_variants = get_winners_day_variants(votes=[*participant_votes[0], *participant_votes[1], *participant_votes[2]], day_count=len(participant_votes[0]))
    # for win_var, day in zip(winner_variants, context["days"]):
    #     assert win_var.id == day["variant_id"]
# def test_trip_itinerary_status_code(client, detailed_session, participant_votes):
#     with capture_template_rendered(client.application) as templates:
#         resp = client.get("trip-itinerary", query_string={"sessionId": 1})
#         assert resp.status_code == 200
#     assert len(templates) == 1
#     template, context = templates[0]
#     assert template.name == "trip-itinerary.html"
#     for key in ("route", "session", "days", "transports", "ya_map_js_api_key"):
#         assert key in context
