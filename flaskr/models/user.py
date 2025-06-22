import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flaskr.models.models import db

if TYPE_CHECKING:
    from flaskr.models.trip import TripParticipant


class User(db.Model):
    uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4()
    )
    name: Mapped[str | None] = mapped_column(default=None)

    sessions: Mapped[list["TripParticipant"]] = relationship(
        back_populates="user"
    )
