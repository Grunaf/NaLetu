from flaskr.models.models import db
from flaskr.models.route import Route


def add_route_db(route: Route):
    db.session.add(route)
    db.session.commit()
