import pytest
from contextlib import contextmanager
from flask import template_rendered
from models import db as db_from_model, Route, RouteCity, City, Day, DayVariant, Segment, TripSession, LodgingOption, POI
from flaskr import create_app
from datetime import datetime as datetime_c
import datetime as datetime_p

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
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})
    yield app


@pytest.fixture
def _db(app):
    print ("_db start")
    db_from_model.init_app(app)
    with app.app_context():
        with app.app_context():
            db_from_model.create_all()
        yield db_from_model
        with app.app_context():
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


@pytest.fixture
def sample_session(_db, add_cities):
    s1 = TripSession(id="e388f4df-8b44-4f92-833d-127b16c3ae4a", route_id="kazan_kavkaz", choices_json="", departure_city_id=3, start_date=datetime_p.date(2025,6,9), end_date=datetime_p.date(2025,6,14))
    r1 = Route(id="kazan_kavkaz", title="Kazan – Kavkaz", duration_days=5, estimated_budget_rub=15000, img='kazan_kavkaz.jpg')
    _db.session.add_all([s1, r1])
    _db.session.commit()

@pytest.fixture
def sample_routes(_db, add_cities):
    # Insert two routes with one city each
    s1 = TripSession(id="e388f4df-8b44-4f92-833d-127b16c3ae4a", route_id="kazan_kavkaz", choices_json="", departure_city_id=3, start_date=datetime_p.date(2025,6,9), end_date=datetime_p.date(2025,6,14))
    r1 = Route(id="kazan_kavkaz", title="Kazan – Kavkaz", duration_days=5, estimated_budget_rub=15000, img='kazan_kavkaz.jpg')
    rc1 = RouteCity(id=3, route_id="kazan_kavkaz", city_id=1, order=1)
    s2 = TripSession(id="e388f4df4-4f92-833d-127b16c3ae4a", route_id="sergiev_posad", choices_json="", departure_city_id=0, start_date=datetime_p.date(2025,6,9), end_date=datetime_p.date(2025,6,14))
    r2 = Route(id="sergiev_posad", title="Sergiev Posad", duration_days=1, estimated_budget_rub=2000, img='sergiev_posad.jpg')
    rc2 = RouteCity(id=4, route_id="sergiev_posad", city_id=2, order=1)

    _db.session.add_all([s1, r1, rc1, s2, r2, rc2])
    _db.session.commit()


@pytest.fixture
def full_route( _db, add_cities):
    route = Route(id='kazan_kavkaz', title='Test Route', duration_days=2,
                      estimated_budget_rub=5000, img='test.jpg')
    _db.session.add(route)

    rc1 = RouteCity(id=1, route_id="kazan_kavkaz", city_id=1, order=1)
    _db.session.add(rc1)

    # 2) Create two Days
    day1 = Day(id=1, day_order=1, route=route)
    day2 = Day(id=2, day_order=2, route=route)
    _db.session.add_all([day1, day2])

    # 3) For each day, one Variant
    var1 = DayVariant(id=1, name='Var 1', est_budget=1000, day=day1)
    var2 = DayVariant(id=2, name='Var 2', est_budget=2000, day=day2)
    _db.session.add_all([var1, var2])

    p1 = POI(name="Казанский кремль", must_see = True, open_time = datetime_p.time.fromisoformat("06:00:00Z"),
              close_time= datetime_p.time.fromisoformat("16:00:00Z"), rating= 4.8, lat = 55.797557, lon = 49.107295)
    p2 = POI(name="Мечеть Кул Шариф", must_see = True, open_time = datetime_p.time.fromisoformat("07:00:00Z"),
              close_time= datetime_p.time.fromisoformat("15:00:00Z"), rating= 4.7, lat = 55.798399, lon = 49.105148)
    
    _db.session.add_all([p1,p2])

    # 4) A couple of POI Segments on each variant
    seg1 = Segment(id=1, variant=var1, type='poi', order=1,
                    start_time=datetime_c.strptime('09:00', '%H:%M').time(), end_time=datetime_c.strptime('10:00', '%H:%M').time(),
                    poi_id=1)
    seg2 = Segment(id=2, variant=var2, type='poi', order=1,
                    start_time=datetime_c.strptime('11:00', '%H:%M').time(), end_time=datetime_c.strptime('12:00', '%H:%M').time(),
                    poi_id=2)
    _db.session.add_all([seg1, seg2])

    # 5) Lodging for var1
    lodge = LodgingOption(id=1, variant_id=var1.id,
                            name='Test Hotel', type='hotel',
                            location_id='loc1', distance_km=0.5,
                            city_id=None)
    _db.session.add(lodge)


    # 7) Create a TripSession pointing at our route
    ses1 = TripSession(
        id='s1',
        route_id=route.id,
        departure_city_id=2,
        start_date=datetime_p.date.fromisoformat('2025-06-01'),
        end_date=datetime_p.date.fromisoformat('2025-06-03'),
        choices_json='[{"day":1,"variant":"v1"}]'
    )
    _db.session.add(ses1)
    _db.session.commit()

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
