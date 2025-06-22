import datetime

from sqlalchemy.orm import Mapped, mapped_column

from .models import db


class PriceEntry(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    object_type: Mapped[str]
    object_id: Mapped[int]
    price: Mapped[int]
    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now(), onupdate=datetime.datetime.now()
    )
