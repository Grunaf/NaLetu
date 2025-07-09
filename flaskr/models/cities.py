from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from slugify import slugify
from sqlalchemy.orm import Mapped, mapped_column

from .models import db


class City(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    lat: Mapped[float]
    lon: Mapped[float]
    location = mapped_column(Geometry("POINT", srid=4326))
    yandex_code: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True)

    def __init__(self, **kvargs):
        super().__init__(**kvargs)
        self.slug = slugify(self.name)
        self.location = from_shape(Point(self.lon, self.lat), srid=4326)

    def __repr__(self):
        return f"Название: {self.name},  Широта: {self.lat}, Долгота: {self.lon}, Местоположение: {self.location}"

    def __str__(self):
        return f"Название: {self.name},  Широта: {self.lat}, Долгота: {self.lon}, Местоположение: {self.location}"
