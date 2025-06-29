import datetime

import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker
from sqlalchemy.orm import Session

from flaskr.models.city import City

# from flaskr.models.meal_place import MealPlace, SimularMealPlaceCache
from flaskr.models.constants import CUISINE, MEAL_PLACE_TYPE, SEGMENT_TYPE
from flaskr.models.meal_place import MealPlace
from flaskr.models.route import POI
from flaskr.models.route import Day, DayVariant, Route, RouteCity, Segment
from flaskr.models.trip import (
    TripInvite,
    TripParticipant,
    TripSession,
    TripVote,
)

# from flaskr.models.trip import (
#     TripInvite,
#     TripParticipant,
#     TripSession,
#     TripVote,
# )
from flaskr.models.user import User
from tests.conftest import db_from_model

faker = Faker("ru_RU")


def generate_date_later(base_date, max_days_after) -> datetime:
    return faker.date_time_between_dates(
        base_date + datetime.timedelta(1),
        base_date + datetime.timedelta(max_days_after),
    )


def generate_time_after(start_time: datetime.time, max_hour: int) -> datetime.time:
    datetime_from_time = datetime.datetime.combine(
        datetime.datetime.today(), start_time
    )
    random_time_after = datetime.timedelta(hours=faker.random_int(min=1, max=max_hour))

    (datetime_from_time + random_time_after).time()
    return


def generate_time(min_hour: int, max_hour: int) -> datetime.time:
    time_iso_format = (
        f"{faker.random_int(min_hour, max_hour):02}:{faker.random_int(0, 59, 20):02}:00"
    )
    return datetime.time.fromisoformat(time_iso_format)


def reset_all_pk_sequences() -> None:
    UserFactory.reset_sequence()
    RouteCityFactory.reset_sequence()
    RouteFactory.reset_sequence()
    CityFactory.reset_sequence()


class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = db_from_model.session

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        session: Session = cls._meta.sqlalchemy_session
        obj = target_class(*args, **kwargs)
        session.add(obj)
        session.commit()
        return obj


class CityFactory(BaseFactory):
    class Meta:
        model = City

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: "Route title #%d" % n)
    lat = faker.latitude()
    lon = faker.longitude()
    yandex_code = "c1234"


class RouteFactory(BaseFactory):
    class Meta:
        model = Route

    id = factory.Sequence(lambda n: n)
    title = factory.Sequence(lambda n: "Route title #%d" % n)
    duration_days = faker.random_int(max=5)
    estimated_budget_rub = faker.random_int(min=1000, max=10000, step=100)
    days = factory.RelatedFactoryList(
        "tests.factories.DayFactory", "route", duration_days
    )
    cities = factory.RelatedFactoryList(
        "tests.factories.RouteCityFactory", "route", 4
    )
    img = faker.uri_path()


class RouteCityFactory(BaseFactory):
    class Meta:
        model = RouteCity

    id = factory.Sequence(lambda n: n)
    city = factory.SubFactory(CityFactory)
    order = 1


class DayFactory(BaseFactory):
    class Meta:
        model = Day

    id = factory.Sequence(lambda n: n)
    day_order = 1
    route = factory.SubFactory(RouteFactory)
    default_variant = factory.RelatedFactory("tests.factories.DayVariantFactory")
    variants = factory.RelatedFactoryList("tests.factories.DayVariantFactory", "day", 3)


class DayVariantFactory(BaseFactory):
    class Meta:
        model = DayVariant

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f"Day variant #{n}")
    est_budget = faker.random_int(min=1000, max=10000, step=100)
    is_default = False


class POIFactory(BaseFactory):
    class Meta:
        model = POI

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f"POI #{n}")
    must_see = faker.boolean(chance_of_getting_true=30)
    open_time = faker.time()
    close_time = faker.time()
    rating = faker.pyfloat(left_digits=1, right_digits=1, max_value=5)
    lat = faker.latitude
    lon = faker.longitude


class SegmentFactory(BaseFactory):
    class Meta:
        model = Segment

    id = factory.Sequence(lambda n: n)
    variant = factory.SubFactory(DayVariantFactory)
    type: int = faker.random_element(SEGMENT_TYPE.keys())
    order = 1
    start_time = generate_time(7, 10)
    end_time = generate_time_after(start_time, 4)
    city = factory.SubFactory(CityFactory)

    class Params:
        is_lodging = factory.Trait(
            lodging_name=factory.Sequence(lambda n: f"Lodging #{n}")
        )
        is_poi = factory.Trait(poi=factory.RelatedFactory(POIFactory, "segment"))
        # is_attached_next_segment = factory.Trait(
        #     attached_next_segment=factory.SubFactory(SegmentFactory)
        # )


class MealPlaceFactory(BaseFactory):
    class Meta:
        model = MealPlace

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f"Meal place #{n}")
    coords = faker.coordinate()
    city = factory.SubFactory(CityFactory)

    type: int = faker.random_element(MEAL_PLACE_TYPE.keys())
    open_time = generate_time(7, 10)
    close_time = generate_time(17, 23)

    cuisine: int = faker.random_element(CUISINE.keys())
    avg_check_rub = faker.random_int(min=100, max=4000, step=120)
    rating = faker.pyfloat(left_digits=1, right_digits=1, max_value=5)
    website = faker.uri_page()

    created_at = faker.date_time()
    updated_at = generate_date_later(created_at, 10)


class UserFactory(BaseFactory):
    class Meta:
        model = User

    uuid = faker.uuid4()
    name = factory.Sequence(lambda n: "User name #%d" % n)


class TripSessionFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = TripSession

    uuid = faker.uuid4()
    departure_city_id = factory.SubFactory(CityFactory)

    start_date = faker.date()
    end_date = faker.date()

    created_at = faker.date_time()


class TripParticipantFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = TripParticipant

    id = factory.Sequence(lambda n: n)
    user = factory.SubFactory(UserFactory)
    session = factory.SubFactory(TripSessionFactory)
    is_admin = False
    join_at = faker.date_time()
