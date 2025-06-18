import datetime as datetime_p
from datetime import datetime as datetime_c
from contextlib import contextmanager
from typing import Generator
import uuid
from flask import template_rendered
from sqlalchemy import text
import sqlalchemy
import pytest

from models.models import db as db_from_model, Route, RouteCity, City, Day, DayVariant, Segment, POI
from models.trip import TripSession, TripParticipant, TripVote, User
from models.meal_place import MealPlace
from flaskr import create_app

# @pytest.fixture
# def app():
#     from models import db
#     app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})
#     db.init_app(app)
#     with app.app_context():
#         with app.app_context():
#             db.create_all()
#         yield app
#         with app.app_context():
#             db.drop_all()

@pytest.fixture
def app():
    app = create_app({
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True,
        "SECRET_KEY": 'fg2131asdhj:Dasdaa0s'})
    yield app

def mock_2gis_request(mocker, data, status=200):
    mock_get = mocker.patch("services.get_f_api_meal_places.requests.get")

    mock_get.return_value.status_code = status
    mock_get.return_value.text = data

@pytest.fixture
def _db(app):
    print ("_db start")
    db_from_model.init_app(app)
    with app.app_context():        
        db_from_model.create_all()
        yield db_from_model
        db_from_model.drop_all()


@pytest.fixture
def client(app, _db):
    print ("client start")
    with app.test_client() as client:
        yield client

@pytest.fixture
def add_cities(_db):
    c1 = City(name="Казань", lat=55.7944, lon=49.111, yandex_code="c43")
    c2 = City(name="Сергиев Посад", lat=56.3, lon=38.1333, yandex_code="c10752")
    c3 = City(name="Москва", lat=22.22, lon=22.22, yandex_code="unknown")
    _db.session.add_all([c1, c2, c3])
    _db.session.commit()
    yield [c1,c2,c3]

@pytest.fixture
def session(_db, add_cities) -> list:
    r1 = Route(id=1, title="Kazan – Kavkaz", duration_days=5, estimated_budget_rub=15000, img='kazan_kavkaz.jpg')
    s1 = TripSession(id=1, uuid=uuid.UUID("ff3251d5-90e0-4f59-b8af-a600fbbb8895"), route_id=1, choices_json="", departure_city_id=3, start_date=datetime_p.date(2025,6,9), end_date=datetime_p.date(2025,6,14))
    _db.session.add_all([s1, r1])
    _db.session.commit()

@pytest.fixture
def sample_routes(_db, add_cities):
    # Insert two routes with one city each
    r1 = Route(id=1, title="Kazan – Kavkaz", duration_days=5, estimated_budget_rub=15000, img='kazan_kavkaz.jpg')
    s1 = TripSession(id=1, uuid=uuid.UUID("ff3251d5-90e0-4f59-b8af-a600fbbb8895"), route_id=1, choices_json="", departure_city_id=3, start_date=datetime_p.date(2025,6,9), end_date=datetime_p.date(2025,6,14))
    rc1 = RouteCity(id=3, route_id=1, city_id=1, order=1)
    s2 = TripSession(id=2, uuid=uuid.UUID("663fc292-951c-4dbc-82fe-b393e0d94a1c"), route_id=2, choices_json="", departure_city_id=0, start_date=datetime_p.date(2025,6,9), end_date=datetime_p.date(2025,6,14))
    r2 = Route(id=2, title="Sergiev Posad", duration_days=1, estimated_budget_rub=2000, img='sergiev_posad.jpg')
    rc2 = RouteCity(id=4, route_id=2, city_id=2, order=1)

    _db.session.add_all([s1, r1, rc1, s2, r2, rc2])
    _db.session.commit()

@pytest.fixture
def poi(_db, add_cities):
    s1 = Segment(variant_id=1, type="poi", order=1,
                start_time=datetime_p.time.fromisoformat("06:00:00Z"),
                end_time=datetime_p.time.fromisoformat("08:00:00Z"), city_id=1, poi_id=1)
    
    p1 = POI(name="Казанский кремль", must_see=True, open_time=datetime_p.time.fromisoformat("06:00:00Z"),
                close_time=datetime_p.time.fromisoformat("16:00:00Z"), rating=4.8, lat=55.797557, lon=49.107295)
    
    _db.session.add_all([s1,p1])
    _db.session.commit()
    yield p1

@pytest.fixture
def meal_places(_db, poi):
    m1 = MealPlace(name="Вкусная Лавка", coords="56.3067,38.1321", cuisine="Кафе",
                    website="https://vk-lavka.ru", avg_check_rub=500,
                    open_time=datetime_p.time.fromisoformat("10:00"), close_time=datetime_p.time.fromisoformat("20:00"),
                    rating=4.2, updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"), city_id=2)
    m2 = MealPlace(name="Пельмешки", coords="56.3091,38.13782", cuisine="Русская",
                    website="https://pelmeshki.ru", avg_check_rub=400,
                    open_time=datetime_p.time.fromisoformat("10:00"), close_time=datetime_p.time.fromisoformat("20:00"),
                    rating=4.1, updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"), city_id=2)
    m3 = MealPlace(name="La Foret", coords="56.3112,38.1392", cuisine="Европейская",
                    website="https://laforet-sp.ru", avg_check_rub=1200,
                    open_time=datetime_p.time.fromisoformat("10:00"), close_time=datetime_p.time.fromisoformat("20:00"),
                    rating=4.5, updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"), city_id=2)
    m4 = MealPlace(name="Дворик у Лавры", coords="56.3075,38.1343", cuisine="Кавказская",
                    website="https://dvoryk-lavra.ru", avg_check_rub=900,
                    open_time=datetime_p.time.fromisoformat("10:00"), close_time=datetime_p.time.fromisoformat("20:00"),
                    rating=4.3, updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"), city_id=2) #another_city
    m5 = MealPlace(name="Рубаи", coords="55.7887,49.1221", cuisine="Узбекская",
                    website="https://rubai.ru", avg_check_rub=800,
                    open_time=datetime_p.time.fromisoformat("10:00"), close_time=datetime_p.time.fromisoformat("20:00"),
                    rating=4.6, updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"), city_id=1) #1.3
    m6 = MealPlace(name="Тюбетей", coords="55.7961,49.1082", cuisine="Татарская",
                    website="https://tubetey.ru", avg_check_rub=500,
                    open_time=datetime_p.time.fromisoformat("10:00"), close_time=datetime_p.time.fromisoformat("20:00"),
                    rating=4.4, updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"), city_id=1) #0.2
    m7 = MealPlace(name="Дрова", coords="55.7980,49.11017", cuisine="Русская",
                    website="https://drova.ru", avg_check_rub=1000,
                    open_time=datetime_p.time.fromisoformat("10:00"), close_time=datetime_p.time.fromisoformat("20:00"),
                    rating=4.3, updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"), city_id=1) #.2
    m8= MealPlace(name="Malabar", coords="55.7964,49.11218", cuisine="Индийская",
                    website="https://malabar-kzn.ru", avg_check_rub=1200,
                    open_time=datetime_p.time.fromisoformat("10:00"), close_time=datetime_p.time.fromisoformat("20:00"),
                    rating=4.7, updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"), city_id=1) #.3 km
    m9 = MealPlace(name="Basilico", coords="55.7978,49.11621", cuisine="Итальянская",
                    website="https://basilico-kzn.ru", avg_check_rub=1500,
                    open_time=datetime_p.time.fromisoformat("10:00"), close_time=datetime_p.time.fromisoformat("20:00"),
                    rating=4.5, updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"), city_id=1) #.5

    _db.session.add_all([m1,m2,m3,m4,m5,m6,m7,m8,m9])
    _db.session.commit()

    yield [m6, m7, m8]

@pytest.fixture
def route(_db, add_cities):
    route = Route(id=1, title='Test Route', duration_days=3,
                      estimated_budget_rub=5000, img='test.jpg')
    _db.session.add(route)
    
    rc1 = RouteCity(id=1, route_id=1, city_id=1, order=1)
    _db.session.add(rc1)
    _db.session.commit()
    yield route

@pytest.fixture
def variants(_db, route):
    day1 = Day(day_order=1, route_id=route.id)
    day2 = Day(day_order=2, route_id=route.id)
    day3 = Day(day_order=3, route_id=route.id)
    _db.session.add_all([day1, day2, day3])
    _db.session.commit()

    var1_1 = DayVariant(name='Var 1_1', est_budget=1200, day_id=day1.id)
    var1_2 = DayVariant(name='Var 1_2', est_budget=1400, day_id=day1.id, is_default=False)
    var2_1 = DayVariant(name='Var 2_1', est_budget=4000, day_id=day2.id)
    var2_2 = DayVariant(name='Var 2_2', est_budget=5000, day_id=day2.id, is_default=False)
    var3_1 = DayVariant(name='Var 3_1', est_budget=1500, day_id=day3.id)
    var3_2 = DayVariant(name='Var 3_2', est_budget=200, day_id=day3.id, is_default=False)
    _db.session.add_all([var1_1, var1_2, var2_1, var2_2, var3_1, var3_2])
    _db.session.commit()
    yield [[var1_1, var1_2], [var2_1, var2_2], [var3_1, var3_2]]

@pytest.fixture
def detail_for_route(_db, variants):
    p1 = POI(name="Казанский кремль", must_see = True, open_time = datetime_p.time.fromisoformat("06:00:00Z"),
              close_time= datetime_p.time.fromisoformat("16:00:00Z"), rating= 4.8, lat = 55.797557, lon = 49.107295)
    p2 = POI(name="Мечеть Кул Шариф", must_see = True, open_time = datetime_p.time.fromisoformat("07:00:00Z"),
              close_time= datetime_p.time.fromisoformat("15:00:00Z"), rating= 4.7, lat = 55.798399, lon = 49.105148)
    
    _db.session.add_all([p1,p2])

    # 4) A couple of POI Segments on each variant
    seg1 = Segment(id=1, variant=variants[0][0], type='poi', order=1,
                    start_time=datetime_c.strptime('09:00', '%H:%M').time(),
                    end_time=datetime_c.strptime('10:00', '%H:%M').time(), poi_id=1)
    seg2 = Segment(id=2, variant=variants[1][0], type='poi', order=1,
                    start_time=datetime_c.strptime('11:00', '%H:%M').time(),
                    end_time=datetime_c.strptime('12:00', '%H:%M').time(), poi_id=2)
    _db.session.add_all([seg1, seg2])

    # 5) Lodging for var1
    # lodge = LodgingOption(id=1, variant_id=variants[0][0].id,
    #                         name='Test Hotel', type='hotel',
    #                         location_id='loc1', distance_km=0.5,
    #                         city_id=None)
    # _db.session.add(lodge)
    _db.session.commit()

@pytest.fixture
def session(_db, route, detail_for_route):
    ses1 = TripSession(
        id=1,
        uuid=uuid.UUID("89151333-7d6a-46fd-bc68-6e69ab9a269e"),
        route_id=route.id,
        departure_city_id=2,
        start_date=datetime_p.date.fromisoformat('2025-06-01'),
        end_date=datetime_p.date.fromisoformat('2025-06-03'),
        choices_json=''
    )
    _db.session.add(ses1)
    _db.session.commit()
    yield ses1

@pytest.fixture
def multiply_sessions(_db, route, session):
    ses2 = TripSession(
        id=2,
        uuid=uuid.UUID("aa773dfa-fac8-4b7a-89dd-3f468a98f87e"),
        route_id=route.id,
        departure_city_id=2,
        start_date=datetime_p.date.fromisoformat('2025-06-01'),
        end_date=datetime_p.date.fromisoformat('2025-06-03'),
        choices_json=''
    )
    ses3 = TripSession(
        id=3,
        uuid=uuid.UUID("7a600248-e0fc-47bd-85a0-1fb518486e81"),
        route_id=route.id,
        departure_city_id=2,
        start_date=datetime_p.date.fromisoformat('2025-06-01'),
        end_date=datetime_p.date.fromisoformat('2025-06-03'),
        choices_json=''
    )
    _db.session.add_all([ses2, ses3])
    _db.session.commit()
    yield [session, ses2, ses3]

@pytest.fixture
def users(_db):
    u1 = User(name="Кирилл", uuid=uuid.UUID("16c9ec5e-90a5-4332-8822-d3a6ccd3c87e"))
    u2 = User(name="Инокентий", uuid=uuid.UUID("35d6f04c-f9d6-4103-8c71-1091f74a6475"))
    u3 = User(name="Кен", uuid=uuid.UUID("2aee1ad6-5f63-4d9e-99bf-9e88f3039b30"))

    _db.session.add_all([u1, u2, u3])
    _db.session.commit()
    yield [u1, u2, u3]

@pytest.fixture
def participants_different_admin_count(_db, users, multiply_sessions): # where Инокентий нигде не админ
    p1 = TripParticipant(user_uuid=users[0].uuid, session_id=multiply_sessions[0].id, join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"))
    p2 = TripParticipant(user_uuid=users[1].uuid, session_id=multiply_sessions[0].id, join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"))
    p3 = TripParticipant(user_uuid=users[2].uuid, session_id=multiply_sessions[0].id, join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"))

    p4 = TripParticipant(user_uuid=users[0].uuid, session_id=multiply_sessions[1].id, join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"))
    p5 = TripParticipant(user_uuid=users[1].uuid, session_id=multiply_sessions[1].id, join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"))
    p6 = TripParticipant(user_uuid=users[2].uuid, session_id=multiply_sessions[1].id, join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"), is_admin=True)

    p7 = TripParticipant(user_uuid=users[1].uuid, session_id=multiply_sessions[2].id, join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"))
    p8 = TripParticipant(user_uuid=users[2].uuid, session_id=multiply_sessions[2].id, join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"), is_admin=True)

    _db.session.add_all([p1, p2, p3, p4, p5, p6, p7, p8])
    _db.session.commit()
    yield [[p1, p2, p3], [p4, p5, p6], [p7, p8]]

@pytest.fixture
def participant_votes(_db, variants, session):
    p1 = TripParticipant(name="Кирилл", session_id=session.id, join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"))
    p2 = TripParticipant(name="Инокентий", session_id=session.id, join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"))
    p3 = TripParticipant(name="Кен", session_id=session.id, join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"))
    _db.session.add_all([p1, p2, p3])
    _db.session.commit()

    p1v1 = TripVote(participant_id=p1.id, variant_id=variants[0][0].id, day_order=0, session_id=session.id, updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"))
    p1v2 = TripVote(participant_id=p1.id, variant_id=variants[1][0].id, day_order=1, session_id=session.id, updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"))
    p1v3 = TripVote(participant_id=p1.id, variant_id=variants[2][0].id, day_order=2, session_id=session.id, updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"))

    p2v1 = TripVote(participant_id=p2.id, variant_id=variants[0][1].id, day_order=0, session_id=session.id, updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"))
    p2v2 = TripVote(participant_id=p2.id, variant_id=variants[1][1].id, day_order=1, session_id=session.id, updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"))
    p2v3 = TripVote(participant_id=p2.id, variant_id=variants[2][1].id, day_order=2, session_id=session.id, updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"))

    p3v1 = TripVote(participant_id=p3.id, variant_id=variants[0][1].id, day_order=0, session_id=session.id, updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"))
    p3v2 = TripVote(participant_id=p3.id, variant_id=variants[1][1].id, day_order=1, session_id=session.id, updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"))
    p3v3 = TripVote(participant_id=p3.id, variant_id=variants[2][1].id, day_order=2, session_id=session.id, updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"))
    _db.session.add_all([p1v1, p1v2, p1v3, p2v1, p2v2, p2v3, p3v1, p3v2, p3v3])
    _db.session.commit()
    yield [[p1v1, p1v2, p1v3], [p2v1, p2v2, p2v3], [p3v1, p3v2, p3v3]]


# @pytest.fixture
# def sample_route(app):
#     with app.app_context():
#         r1 = Route(id="kazan_kavkaz", title="Kazan – Kavkaz", duration_days=5, estimated_budget_rub=15000, img='kazan_kavkaz.jpg')
#         db.session.add(r1)
#         db.session.commit()

# @pytest.fixture
# def sample_routes(app):
#     # Insert two routes with one city each
#     r1 = Route(id="kazan_kavkaz", title="Kazan – Kavkaz", duration_days=5, estimated_budget_rub=15000, img='kazan_kavkaz.jpg')
#     c1 = RouteCity(id=3, route_id="kazan_kavkaz", name="Kazan", lat=55.7944, lon=49.1110, station_code=None, order=1)
#     r2 = Route(id="sergiev_posad", title="Sergiev Posad", duration_days=1, estimated_budget_rub=2000, img='sergiev_posad.jpg')
#     c2 = RouteCity(id=4, route_id="sergiev_posad", name="Sergiev Posad", lat=56.3000, lon=38.1333, station_code=None, order=1)
#     db.session.add(r1)
#     db.session.add(c1)
#     db.session.add(r2)
#     db.session.add(c2)
#     db.session.commit()

# @pytest.fixture
# def full_route(app):
#     route = Route(id='kazan_kavkaz', title='Test Route', duration_days=2,
#                       estimated_budget_rub=5000, img='test.jpg')
#     db.session.add(route)

#     c1 = RouteCity(id=1, route_id="kazan_kavkaz", name="Kazan", lat=55.7944, lon=49.1110, station_code=None, order=1)
#     db.session.add(c1)

#     # 2) Create two Days
#     day1 = Day(id=1, day_order=1, route=route)
#     day2 = Day(id=2, day_order=2, route=route)
#     db.session.add_all([day1, day2])

#     # 3) For each day, one Variant
#     var1 = DayVariant(id=1, variant_id='v1', name='Var 1', est_budget=1000, day=day1)
#     var2 = DayVariant(id=2, variant_id='v2', name='Var 2', est_budget=2000, day=day2)
#     db.session.add_all([var1, var2])

#     # 4) A couple of POI Segments on each variant
#     seg1 = Segment(id=1, variant=var1, type='poi', order=1,
#                     start_time=datetime_c.strptime('09:00', '%H:%M').time(), end_time=datetime_c.strptime('10:00', '%H:%M').time(),
#                     poi_name='POI A', arrival_window='09:00–10:00',
#                     rating=4.5)
#     seg2 = Segment(id=2, variant=var2, type='poi', order=1,
#                     start_time=datetime_c.strptime('11:00', '%H:%M').time(), end_time=datetime_c.strptime('12:00', '%H:%M').time(),
#                     poi_name='POI B', arrival_window='11:00–12:00',
#                     rating=4.7)
#     db.session.add_all([seg1, seg2])

#     # 5) Lodging for var1
#     lodge = LodgingOption(id=1, variant_id=var1.id,
#                             name='Test Hotel', type='hotel',
#                             location_id='loc1', distance_km=0.5,
#                             city_id=None)
#     db.session.add(lodge)

#     # 6) Transport options for the route
#     t1 = TransportOption(id=1, route_id=route.id, mode='bus',
#                             start_city_id=1, end_city_id=1,
#                             start_time_min=60, start_cost_rub=500,
#                             end_time_min=60, end_cost_rub=500)
#     db.session.add(t1)

#     # 7) Create a TripSession pointing at our route
#     ses1 = TripSession(
#         id='s1',
#         route_id=route.id,
#         departure_city='Moscow',
#         departure_lat=55.75,
#         departure_lon=37.61,
#         check_in=datetime_p.date.fromisoformat('2025-06-01'),
#         check_out=datetime_p.date.fromisoformat('2025-06-03'),
#         choices_json='[{"day":1,"variant":"v1"}]'
#     )
#     db.session.add(ses1)
#     db.session.commit()

@contextmanager
def capture_template_rendered(app):
    recorded = []
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)
