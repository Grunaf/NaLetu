import datetime as datetime_p
import os
import uuid
from contextlib import contextmanager
from datetime import datetime as datetime_c
from typing import Generator

import pytest
from flask import template_rendered
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import delete, text
from testcontainers.postgres import PostgresContainer

from flaskr import create_app
from flaskr.models.city import City
from flaskr.models.meal_place import MealPlace, SimularMealPlaceCache
from flaskr.models.models import db as db_from_model
from flaskr.models.route import POI
from flaskr.models.route import Day, DayVariant, Route, RouteCity, Segment
from flaskr.models.transport import TransportCache
from flaskr.models.trip import (
    TripInvite,
    TripParticipant,
    TripSession,
    TripVote,
)
from flaskr.models.user import User
from tests.factories import (
    # RouteCityFactory,
    RouteFactory,
    # TripParticipantFactory,
    # TripSessionFactory,
    UserFactory,
)

postgres = PostgresContainer("postgres:16-alpine")


@pytest.fixture(scope="module")
def setup(request):
    postgres.start()

    def remove_container():
        postgres.stop()

    request.addfinalizer(remove_container)
    db_host = postgres.get_container_host_ip()
    db_port = postgres.get_exposed_port(5432)
    db_user = postgres.username
    db_password = postgres.password
    db_name = postgres.dbname

    os.environ["DB_CONN"] = postgres.get_connection_url()
    os.environ["DB_HOST"] = db_host
    os.environ["DB_PORT"] = db_port
    os.environ["DB_USERNAME"] = db_user
    os.environ["DB_PASSWORD"] = db_password
    os.environ["DB_NAME"] = db_name

    yield {
        "db_host": db_host,
        "db_port": db_port,
        "db_user": db_user,
        "db_password": db_password,
        "db_name": db_name,
    }


@pytest.fixture(scope="module")
def app(setup):
    app = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": f"postgresql://{setup['db_user']}:{setup['db_password']}@{setup['db_host']}:{setup['db_port']}/{setup['db_name']}",
            "TESTING": True,
            "SECRET_KEY": "fg2131asdhj:Dasdaa0s",
        }
    )

    yield app


@pytest.fixture(scope="module")
def _db(app):
    db_from_model.init_app(app)
    with app.app_context():
        db_from_model.create_all()
        yield db_from_model


def delete_entries(table, tableNameUnderscore="", update_seq=True):
    stmt = delete(table)
    db_from_model.session.execute(stmt.execution_options(synchronize_session=False))

    if update_seq:
        stmt = text(f"ALTER SEQUENCE {tableNameUnderscore}_id_seq RESTART WITH 1")
        db_from_model.session.execute(stmt)

    db_from_model.session.expunge_all()
    db_from_model.session.commit()


@pytest.fixture(scope="function", autouse=True)
def setup_data(_db: SQLAlchemy):
    delete_entries(TripVote, "trip_vote")
    delete_entries(TripParticipant, "trip_participant")
    delete_entries(TransportCache, "transport_cache")
    delete_entries(TripInvite, update_seq=False)
    delete_entries(TripSession, "trip_session")

    delete_entries(SimularMealPlaceCache, "simular_meal_place_cache")
    delete_entries(MealPlace, "meal_place")
    delete_entries(Segment, "segment")
    delete_entries(POI, "poi")
    delete_entries(DayVariant, "day_variant")
    delete_entries(Day, "day")

    delete_entries(User, update_seq=False)
    delete_entries(RouteCity, "route_city")
    delete_entries(Route, "route")
    delete_entries(City, "city")


def mock_2gis_request(mocker, data, status=200):
    mock_get = mocker.patch("services.get_f_api_meal_places.requests.get")

    mock_get.return_value.status_code = status
    mock_get.return_value.text = data


# # register(RouteFactory)
# # register(RouteCityFactory)
# # register(TripParticipantFactory)
# # register(TripSessionFactory)
# register(UserFactory)


@pytest.fixture
def client(app, _db):
    with app.test_client() as client:
        yield client


@pytest.fixture()
def add_cities(_db):
    c1 = City(name="Казань", lat=55.7944, lon=49.111, yandex_code="c43")
    c2 = City(name="Сергиев Посад", lat=56.3, lon=38.1333, yandex_code="c10752")
    c3 = City(name="Москва", lat=22.22, lon=22.22, yandex_code="unknown")
    _db.session.add_all([c1, c2, c3])
    _db.session.commit()
    yield [c1, c2, c3]


@pytest.fixture
def route(_db, add_cities):
    route = Route(
        id=1,
        title="Test Route",
        duration_days=3,
        estimated_budget_rub=5000,
        img="test.jpg",
    )
    _db.session.add(route)
    _db.session.commit()
    rc1 = RouteCity(id=1, route_id=route.id, city_id=add_cities[0].id, order=1)
    _db.session.add(rc1)
    _db.session.commit()
    yield route


@pytest.fixture
def session(_db, routes, add_cities, detail_for_route):
    ses1 = TripSession(
        uuid=uuid.UUID("89151333-7d6a-46fd-bc68-6e69ab9a269e"),
        route_id=routes[0].id,
        departure_city_id=add_cities[1].id,
        start_date=datetime_p.date.fromisoformat("2025-06-01"),
        end_date=datetime_p.date.fromisoformat("2025-06-03"),
    )
    _db.session.add(ses1)
    _db.session.commit()
    yield ses1


@pytest.fixture
def routes(_db, route, add_cities):
    r2 = Route(
        id=2,
        title="Test Route 2",
        duration_days=3,
        estimated_budget_rub=15000,
        img="test.jpg",
    )
    r3 = Route(
        id=3,
        title="Test Route 3",
        duration_days=3,
        estimated_budget_rub=15000,
        img="test.jpg",
    )
    _db.session.add_all([r2, r3])
    _db.session.commit()

    rc2 = RouteCity(id=2, route_id=r2.id, city_id=add_cities[0].id, order=1)
    rc3 = RouteCity(id=3, route_id=r3.id, city_id=add_cities[0].id, order=1)

    _db.session.add_all([rc2, rc3])
    _db.session.commit()
    yield [route, r2, r3]


@pytest.fixture
def sample_routes(_db, cities):
    # Insert two routes with one city each
    r1 = RouteFactory.create(
        id=1,
        title="Kazan – Kavkaz",
        duration_days=5,
        estimated_budget_rub=15000,
        img="kazan_kavkaz.jpg",
    )
    s1 = TripSession(
        id=1,
        uuid=uuid.UUID("ff3251d5-90e0-4f59-b8af-a600fbbb8895"),
        route_id=1,
        departure_city_id=add_cities[2].id,
        start_date=datetime_p.date(2025, 6, 9),
        end_date=datetime_p.date(2025, 6, 14),
    )
    rc1 = RouteCity(id=3, route_id=1, city_id=1, order=1)

    s2 = TripSession(
        id=2,
        uuid=uuid.UUID("663fc292-951c-4dbc-82fe-b393e0d94a1c"),
        route_id=2,
        departure_city_id=add_cities[0].id,
        start_date=datetime_p.date(2025, 6, 9),
        end_date=datetime_p.date(2025, 6, 14),
    )
    r2 = RouteFactory.create_batch(
        id=2,
        title="Sergiev Posad",
        duration_days=1,
        estimated_budget_rub=2000,
        img="sergiev_posad.jpg",
    )
    rc2 = RouteCity(id=4, route_id=2, city_id=2, order=1)


@pytest.fixture
def days(_db, route):
    day1 = Day(day_order=1, route_id=route.id)
    day2 = Day(day_order=2, route_id=route.id)
    day3 = Day(day_order=3, route_id=route.id)

    _db.session.add_all([day1, day2, day3])
    _db.session.commit()
    yield [day1, day2, day3]


@pytest.fixture
def variants(_db, days):
    var1_1 = DayVariant(name="Var 1_1", est_budget=1200, day_id=days[0].id)
    var1_2 = DayVariant(
        name="Var 1_2", est_budget=1400, day_id=days[0].id, is_default=False
    )
    var2_1 = DayVariant(name="Var 2_1", est_budget=4000, day_id=days[1].id)
    var2_2 = DayVariant(
        name="Var 2_2", est_budget=5000, day_id=days[1].id, is_default=False
    )
    var3_1 = DayVariant(name="Var 3_1", est_budget=1500, day_id=days[2].id)
    var3_2 = DayVariant(
        name="Var 3_2", est_budget=200, day_id=days[2].id, is_default=False
    )

    _db.session.add_all([var1_1, var1_2, var2_1, var2_2, var3_1, var3_2])
    _db.session.commit()
    yield [[var1_1, var1_2], [var2_1, var2_2], [var3_1, var3_2]]


@pytest.fixture
def poi(_db, variants, add_cities):
    s1 = Segment(
        variant_id=variants[0][0].id,
        type="poi",
        order=1,
        start_time=datetime_p.time.fromisoformat("06:00:00Z"),
        end_time=datetime_p.time.fromisoformat("08:00:00Z"),
        city_id=1,
        poi_id=1,
    )

    p1 = POI(
        name="Казанский кремль",
        must_see=True,
        open_time=datetime_p.time.fromisoformat("06:00:00Z"),
        close_time=datetime_p.time.fromisoformat("16:00:00Z"),
        rating=4.8,
        lat=55.797557,
        lon=49.107295,
    )

    _db.session.add_all([s1, p1])
    _db.session.commit()
    yield p1


@pytest.fixture
def meal_places(_db, poi):
    m1 = MealPlace(
        name="Вкусная Лавка",
        coords="56.3067,38.1321",
        cuisine="Кафе",
        website="https://vk-lavka.ru",
        avg_check_rub=500,
        open_time=datetime_p.time.fromisoformat("10:00"),
        close_time=datetime_p.time.fromisoformat("20:00"),
        rating=4.2,
        updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"),
        city_id=2,
    )
    m2 = MealPlace(
        name="Пельмешки",
        coords="56.3091,38.13782",
        cuisine="Русская",
        website="https://pelmeshki.ru",
        avg_check_rub=400,
        open_time=datetime_p.time.fromisoformat("10:00"),
        close_time=datetime_p.time.fromisoformat("20:00"),
        rating=4.1,
        updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"),
        city_id=2,
    )
    m3 = MealPlace(
        name="La Foret",
        coords="56.3112,38.1392",
        cuisine="Европейская",
        website="https://laforet-sp.ru",
        avg_check_rub=1200,
        open_time=datetime_p.time.fromisoformat("10:00"),
        close_time=datetime_p.time.fromisoformat("20:00"),
        rating=4.5,
        updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"),
        city_id=2,
    )
    m4 = MealPlace(
        name="Дворик у Лавры",
        coords="56.3075,38.1343",
        cuisine="Кавказская",
        website="https://dvoryk-lavra.ru",
        avg_check_rub=900,
        open_time=datetime_p.time.fromisoformat("10:00"),
        close_time=datetime_p.time.fromisoformat("20:00"),
        rating=4.3,
        updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"),
        city_id=2,
    )  # another_city
    m5 = MealPlace(
        name="Рубаи",
        coords="55.7887,49.1221",
        cuisine="Узбекская",
        website="https://rubai.ru",
        avg_check_rub=800,
        open_time=datetime_p.time.fromisoformat("10:00"),
        close_time=datetime_p.time.fromisoformat("20:00"),
        rating=4.6,
        updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"),
        city_id=1,
    )  # 1.3
    m6 = MealPlace(
        name="Тюбетей",
        coords="55.7961,49.1082",
        cuisine="Татарская",
        website="https://tubetey.ru",
        avg_check_rub=500,
        open_time=datetime_p.time.fromisoformat("10:00"),
        close_time=datetime_p.time.fromisoformat("20:00"),
        rating=4.4,
        updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"),
        city_id=1,
    )  # 0.2
    m7 = MealPlace(
        name="Дрова",
        coords="55.7980,49.11017",
        cuisine="Русская",
        website="https://drova.ru",
        avg_check_rub=1000,
        open_time=datetime_p.time.fromisoformat("10:00"),
        close_time=datetime_p.time.fromisoformat("20:00"),
        rating=4.3,
        updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"),
        city_id=1,
    )  # .2
    m8 = MealPlace(
        name="Malabar",
        coords="55.7964,49.11218",
        cuisine="Индийская",
        website="https://malabar-kzn.ru",
        avg_check_rub=1200,
        open_time=datetime_p.time.fromisoformat("10:00"),
        close_time=datetime_p.time.fromisoformat("20:00"),
        rating=4.7,
        updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"),
        city_id=1,
    )  # .3 km
    m9 = MealPlace(
        name="Basilico",
        coords="55.7978,49.11621",
        cuisine="Итальянская",
        website="https://basilico-kzn.ru",
        avg_check_rub=1500,
        open_time=datetime_p.time.fromisoformat("10:00"),
        close_time=datetime_p.time.fromisoformat("20:00"),
        rating=4.5,
        updated_at=datetime_p.datetime.fromisoformat("2025-06-11 16:44:15.375"),
        city_id=1,
    )  # .5

    _db.session.add_all([m1, m2, m3, m4, m5, m6, m7, m8, m9])
    _db.session.commit()

    yield [m6, m7, m8]


@pytest.fixture
def detail_for_route(_db, variants):
    p1 = POI(
        name="Казанский кремль",
        must_see=True,
        open_time=datetime_p.time.fromisoformat("06:00:00Z"),
        close_time=datetime_p.time.fromisoformat("16:00:00Z"),
        rating=4.8,
        lat=55.797557,
        lon=49.107295,
    )
    p2 = POI(
        name="Мечеть Кул Шариф",
        must_see=True,
        open_time=datetime_p.time.fromisoformat("07:00:00Z"),
        close_time=datetime_p.time.fromisoformat("15:00:00Z"),
        rating=4.7,
        lat=55.798399,
        lon=49.105148,
    )

    _db.session.add_all([p1, p2])

    # 4) A couple of POI Segments on each variant
    seg1 = Segment(
        id=1,
        variant_id=variants[0][0].id,
        type="poi",
        order=1,
        start_time=datetime_c.strptime("09:00", "%H:%M").time(),
        end_time=datetime_c.strptime("10:00", "%H:%M").time(),
        poi_id=1,
    )
    seg2 = Segment(
        id=2,
        variant_id=variants[1][0].id,
        type="poi",
        order=1,
        start_time=datetime_c.strptime("11:00", "%H:%M").time(),
        end_time=datetime_c.strptime("12:00", "%H:%M").time(),
        poi_id=2,
    )
    _db.session.add_all([seg1, seg2])

    # 5) Lodging for var1
    # lodge = LodgingOption(id=1, variant_id=variants[0][0].id,
    #                         name='Test Hotel', type='hotel',
    #                         location_id='loc1', distance_km=0.5,
    #                         city_id=None)
    # db_from_model.session.add(lodge)
    _db.session.commit()


@pytest.fixture
def session(_db, routes, add_cities, detail_for_route):
    ses1 = TripSession(
        uuid=uuid.UUID("89151333-7d6a-46fd-bc68-6e69ab9a269e"),
        route_id=routes[0].id,
        departure_city_id=add_cities[1].id,
        start_date=datetime_p.date.fromisoformat("2025-06-01"),
        end_date=datetime_p.date.fromisoformat("2025-06-03"),
    )
    _db.session.add(ses1)
    _db.session.commit()
    yield ses1


@pytest.fixture
def multiply_sessions(
    _db, routes, add_cities, session
) -> Generator[list[TripSession], None, None]:
    ses2 = TripSession(
        uuid=uuid.UUID("aa773dfa-fac8-4b7a-89dd-3f468a98f87e"),
        route_id=routes[1].id,
        departure_city_id=add_cities[1].id,
        start_date=datetime_p.date.fromisoformat("2025-06-01"),
        end_date=datetime_p.date.fromisoformat("2025-06-03"),
    )
    ses3 = TripSession(
        uuid=uuid.UUID("7a600248-e0fc-47bd-85a0-1fb518486e81"),
        route_id=routes[2].id,
        departure_city_id=add_cities[1].id,
        start_date=datetime_p.date.fromisoformat("2025-06-01"),
        end_date=datetime_p.date.fromisoformat("2025-06-03"),
    )
    _db.session.add_all([ses2, ses3])
    _db.session.commit()
    yield [session, ses2, ses3]


@pytest.fixture
def users(_db):
    u1 = User(name="Кирилл", uuid=uuid.UUID("16c9ec5e-90a5-4332-8822-d3a6ccd3c87e"))
    u2 = User(
        name="Инокентий",
        uuid=uuid.UUID("35d6f04c-f9d6-4103-8c71-1091f74a6475"),
    )
    u3 = User(name="Кен", uuid=uuid.UUID("2aee1ad6-5f63-4d9e-99bf-9e88f3039b30"))
    u4 = User(name="Кенилана", uuid=uuid.UUID("2dc89be5-8167-4894-922c-005b09a6ebc1"))

    _db.session.add_all([u1, u2, u3, u4])
    _db.session.commit()
    yield [u1, u2, u3, u4]


@pytest.fixture
def participants_for_session(
    _db, users, session
) -> Generator[
    list[list[TripParticipant]], None, None
]:  # where Инокентий нигде не админ
    p1 = TripParticipant(
        user_uuid=users[0].uuid,
        session_id=session.id,
        join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"),
        is_admin=True,
    )
    p2 = TripParticipant(
        user_uuid=users[1].uuid,
        session_id=session.id,
        join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"),
        is_admin=False,
    )
    p3 = TripParticipant(
        user_uuid=users[2].uuid,
        session_id=session.id,
        join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"),
        is_admin=False,
    )

    _db.session.add_all([p1, p2, p3])
    _db.session.commit()
    yield [p1, p2, p3]


@pytest.fixture
def participants_different_admin_count(
    _db, users, participants_for_session, multiply_sessions
) -> Generator[
    list[list[TripParticipant]], None, None
]:  # where Инокентий нигде не админ
    p4 = TripParticipant(
        user_uuid=users[0].uuid,
        session_id=multiply_sessions[1].id,
        join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"),
        is_admin=False,
    )
    p5 = TripParticipant(
        user_uuid=users[1].uuid,
        session_id=multiply_sessions[1].id,
        join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"),
        is_admin=False,
    )
    p6 = TripParticipant(
        user_uuid=users[2].uuid,
        session_id=multiply_sessions[1].id,
        join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"),
        is_admin=True,
    )

    p7 = TripParticipant(
        user_uuid=users[1].uuid,
        session_id=multiply_sessions[2].id,
        join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"),
        is_admin=False,
    )
    p8 = TripParticipant(
        user_uuid=users[2].uuid,
        session_id=multiply_sessions[2].id,
        join_at=datetime_c.fromisoformat("2025-06-09 16:07:35.989"),
        is_admin=True,
    )

    _db.session.add_all([p4, p5, p6, p7, p8])
    _db.session.commit()
    yield [
        [
            participants_for_session[0],
            participants_for_session[1],
            participants_for_session[2],
        ],
        [p4, p5, p6],
        [p7, p8],
    ]


@pytest.fixture
def trip_invites(
    _db: SQLAlchemy, multiply_sessions, participants_different_admin_count
):
    ti1 = TripInvite(uuid=uuid.uuid4(), session_uuid=multiply_sessions[0].uuid)
    ti2 = TripInvite(
        uuid=uuid.uuid4(),
        session_uuid=multiply_sessions[1].uuid,
        is_active=False,
    )
    ti3 = TripInvite(uuid=uuid.uuid4(), session_uuid=multiply_sessions[2].uuid)
    ti4 = TripInvite(
        uuid=uuid.uuid4(),
        session_uuid=multiply_sessions[2].uuid,
        is_active=False,
    )

    _db.session.add_all([ti1, ti2, ti3, ti4])
    _db.session.commit()
    yield [ti1, ti2, ti3, ti4]


@pytest.fixture
def participant_votes(_db, variants, session, participants_for_session):
    p1v1 = TripVote(
        participant_id=participants_for_session[0].id,
        variant_id=variants[0][0].id,
        day_order=0,
        session_id=session.id,
        updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"),
    )
    p1v2 = TripVote(
        participant_id=participants_for_session[0].id,
        variant_id=variants[1][0].id,
        day_order=1,
        session_id=session.id,
        updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"),
    )
    p1v3 = TripVote(
        participant_id=participants_for_session[0].id,
        variant_id=variants[2][0].id,
        day_order=2,
        session_id=session.id,
        updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"),
    )

    p2v1 = TripVote(
        participant_id=participants_for_session[1].id,
        variant_id=variants[0][1].id,
        day_order=0,
        session_id=session.id,
        updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"),
    )
    p2v2 = TripVote(
        participant_id=participants_for_session[1].id,
        variant_id=variants[1][1].id,
        day_order=1,
        session_id=session.id,
        updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"),
    )
    p2v3 = TripVote(
        participant_id=participants_for_session[1].id,
        variant_id=variants[2][1].id,
        day_order=2,
        session_id=session.id,
        updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"),
    )

    p3v1 = TripVote(
        participant_id=participants_for_session[2].id,
        variant_id=variants[0][1].id,
        day_order=0,
        session_id=session.id,
        updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"),
    )
    p3v2 = TripVote(
        participant_id=participants_for_session[2].id,
        variant_id=variants[1][1].id,
        day_order=1,
        session_id=session.id,
        updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"),
    )
    p3v3 = TripVote(
        participant_id=participants_for_session[2].id,
        variant_id=variants[2][1].id,
        day_order=2,
        session_id=session.id,
        updated_at=datetime_c.fromisoformat("2025-06-09 23:32:02.161"),
    )

    _db.session.add_all([p1v1, p1v2, p1v3, p2v1, p2v2, p2v3, p3v1, p3v2, p3v3])
    _db.session.commit()
    yield [[p1v1, p1v2, p1v3], [p2v1, p2v2, p2v3], [p3v1, p3v2, p3v3]]


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
