from sqlalchemy.orm import Mapped, mapped_column, relationship
from .models import db


class City(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    lat: Mapped[float]
    lon: Mapped[float]
    yandex_code: Mapped[str]

    route_cities: Mapped["RouteCity"] = relationship(
        "RouteCity",
        back_populates="city"
        )
