from flask import Blueprint
from flask_migrate import downgrade, upgrade
from sqlalchemy import text

from flaskr.models.models import db

mod = Blueprint("shell", __name__)


def seed_db(file_seed: str = "initial_data.sql") -> None:
    db.create_all()
    with open(file_seed, encoding="UTF-8") as file:
        db.session.execute(text(file.read()))
    db.session.commit()


@mod.cli.command("reset-db")
def reset_db() -> None:
    print("Dropping all tables")
    downgrade(revision="base")
    print("Upgrading")
    upgrade()
    print("Seeding")
    seed_db()
