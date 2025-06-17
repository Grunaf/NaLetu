import uuid
from models.models import DayVariant, db, Route, City
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, JSON
import datetime

class TripSession(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    route_id: Mapped[int] = mapped_column(ForeignKey("route.id"))
    departure_city_id: Mapped[int] = mapped_column(ForeignKey("city.id"))

    start_date: Mapped[datetime.date] 
    end_date: Mapped[datetime.date]
    choices_json: Mapped[JSON] = mapped_column(type_=JSON)

    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now())
    participants: Mapped[list["TripParticipant"]] = relationship(back_populates="session")
    route: Mapped["Route"] = relationship()
    city: Mapped["City"] = relationship()

class TripParticipant(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    session_id: Mapped[int] = mapped_column(ForeignKey("trip_session.id"))

    join_at: Mapped[datetime.datetime] = db.Column(db.DateTime, default=datetime.datetime.now())
    session: Mapped["TripSession"] = relationship(back_populates="participants")
    votes: Mapped[list["TripVote"]] = relationship(back_populates="participant")

class TripVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("trip_session.id"))
    variant_id: Mapped[int] = mapped_column(ForeignKey("day_variant.id"))
    participant_id: Mapped[int] = mapped_column(ForeignKey("trip_participant.id"))
    day_order: Mapped[int]
    updated_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now(), onupdate=datetime.datetime.now())

    day_variant: Mapped["DayVariant"] = relationship()
    participant: Mapped["TripParticipant"] = relationship(back_populates="votes")

