import datetime

import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from flaskr.models.cities import City

# from flaskr.models.meal_place import MealPlace, SimularMealPlaceCache
from flaskr.models.constants import CUISINE, MEAL_PLACE_TYPE, SEGMENT_TYPE
from flaskr.models.meal_place import MealPlace
from flaskr.models.route import POI
from flaskr.models.route import Day, DayVariant, Route, RouteCity, Segment
from flaskr.models.trip import (
    TripParticipant,
    TripSession,
)

from flaskr.models.user import Traveler
from tests.conftest import db_from_model

faker = Faker("ru_RU")
faker_uuid_no_cast = lambda: faker.uuid4(cast_to=None)


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
    RouteCityFactory.reset_sequence()
    RouteFactory.reset_sequence()
    CityFactory.reset_sequence()


class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = db_from_model.session
        sqlalchemy_session_persistence = "commit"


class CityFactory(BaseFactory):
    class Meta:
        model = City

    name = factory.Sequence(lambda n: "City title #%d" % n)
    lat = factory.LazyFunction(faker.latitude)
    lon = factory.LazyFunction(faker.longitude)
    location = factory.LazyAttribute(
        lambda city: from_shape(Point(city.lon, city.lat), srid=4326)
    )
    yandex_code = "c1234"
    slug = faker.slug()


class RouteFactory(BaseFactory):
    class Meta:
        model = Route

    title = factory.Sequence(lambda n: "Route title #%d" % n)
    duration_days = factory.LazyFunction(lambda: faker.random_int(max=5))
    estimated_budget_rub = factory.LazyFunction(
        lambda: faker.random_int(min=1000, max=10000, step=100)
    )
    img = faker.uri_path()

    @factory.post_generation
    def cities(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            created_route_cities = []
            for i in range(extracted):
                created_route_cities.append(
                    RouteCityFactory(route=self, order=i + 1, **kwargs)
                )

            if created_route_cities:
                self.start_city = created_route_cities[0]
                BaseFactory._meta.sqlalchemy_session.commit()
        else:
            RouteCityFactory(route=self, **kwargs)

    @factory.post_generation
    def days(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for i in range(self.duration_days):
                DayFactory(route=self, day_order=i + 1, **kwargs)
        else:
            DayFactory(route=self, **kwargs)


class RouteCityFactory(BaseFactory):
    class Meta:
        model = RouteCity

    city = factory.SubFactory(CityFactory)
    route = None
    order = 1


class DayFactory(BaseFactory):
    class Meta:
        model = Day

    day_order = 1
    route = factory.SubFactory(RouteFactory)
    variants = factory.RelatedFactoryList("tests.factories.DayVariantFactory", "day", 3)


class DayVariantFactory(BaseFactory):
    class Meta:
        model = DayVariant

    name = factory.Sequence(lambda n: f"Day variant #{n}")
    est_budget = faker.random_int(min=1000, max=10000, step=100)
    is_default = False
    day = None


class POIFactory(BaseFactory):
    class Meta:
        model = POI

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


class TravelerFactory(BaseFactory):
    class Meta:
        model = Traveler

    uuid = factory.LazyFunction(faker_uuid_no_cast)
    name = factory.Sequence(lambda n: "User name #%d" % n)


class TripSessionFactory(BaseFactory):
    class Meta:
        model = TripSession

    uuid = factory.LazyFunction(faker_uuid_no_cast)
    departure_city_id = factory.SubFactory(CityFactory)

    start_date = factory.LazyFunction(faker.date)
    end_date = factory.LazyFunction(faker.date)

    created_at = factory.LazyFunction(faker.date_time)
    route = factory.SubFactory(RouteFactory)
    city = factory.SubFactory(CityFactory)


class TripParticipantFactory(BaseFactory):
    class Meta:
        model = TripParticipant

    user = factory.SubFactory(TravelerFactory)
    session = factory.SubFactory(TripSessionFactory)
    is_admin = False
    join_at = faker.date_time()
