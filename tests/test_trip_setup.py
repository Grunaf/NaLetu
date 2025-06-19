
# def test_open_voting_page_if_joined(add_cities, routes, users, multiply_sessions, participants_different_admin_count, client):   
#     """
#     Если пользователь перешел на страницу голосования, к которой он присоединен,
#     то открываем страницу
#     """
#     with client.session_transaction() as session:
#         session["uuid"] = users[2].uuid # устанавливаем uuid пользователя, у которого есть доступ к поездке

#     resp = client.get("/trip-setup/", query_string={"sessionId": multiply_sessions[2].id}) # переходим по карточке route
    
#     assert resp.status_code == 200 # успешно