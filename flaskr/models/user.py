import uuid as module_uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flaskr.models.constants import ADMIN, APPROVED, MODERATOR, NEW
from flaskr.models.models import DataEntryMixin, db

if TYPE_CHECKING:
    from flaskr.models.trip import TripParticipant


class UserMixin:
    uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=module_uuid.uuid4
    )
    name: Mapped[str | None] = mapped_column(default=None)


class Traveler(UserMixin, db.Model):
    __tablename__ = "traveler"
    participations: Mapped[list["TripParticipant"]] = relationship(
        back_populates="user"
    )


class Staff(UserMixin, db.Model):
    __tablename__ = "staff"

    first_name: Mapped[str]
    last_name: Mapped[str]
    login: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    role: Mapped[int] = mapped_column(SmallInteger, default=MODERATOR)
    request: Mapped["AdditionRequest"] = relationship(back_populates="staff")

    @property
    def is_admin(self):
        return self.role == ADMIN

    @property
    def is_moderator(self):
        return self.role == MODERATOR

    @property
    def is_authenticated(self):
        return self.is_admin or (self.is_moderator and self.request.status == APPROVED)

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.uuid

    def __unicode__(self):
        return self.username


class AdditionRequest(DataEntryMixin, db.Model):
    __tablename__ = "addition_request"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=NEW)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.uuid"))

    staff: Mapped[Staff] = relationship(back_populates="request")
