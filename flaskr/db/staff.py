from uuid import UUID

from sqlalchemy import select

from flaskr.models.models import db
from flaskr.models.user import Staff


def get_staff(uuid: UUID):
    stmt = select(Staff).where(Staff.uuid == uuid)
    return db.session.execute(stmt).scalars().first()
