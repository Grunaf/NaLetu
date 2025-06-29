from flask_admin import Admin
from flaskr.admin.views import (
    AdminModelView,
    AssembleRouteView,
    MyAdminIndexView,
    MyModeratorIndexView,
    TravelerView,
)
from flaskr.models.meal_place import MealPlace, SimularMealPlaceCache
from flaskr.models.models import db
from flaskr.models.route import POI, Day, DayVariant, Route, Segment
from flaskr.models.trip import (
    TripInvite,
    TripParticipant,
    TripSession,
    TripVote,
)
from flaskr.models.user import AdditionRequest, Staff, Traveler

admin = Admin(
    name="Admin-panel",
    index_view=MyAdminIndexView(endpoint="admin", url="/admin"),
    template_mode="bootstrap4",
)
moderator = Admin(
    name="Operator-panel",
    template_mode="bootstrap4",
    index_view=MyModeratorIndexView(endpoint="moderator", url="/moderator"),
)


def setup_admin(app):
    admin.init_app(app)
    moderator.init_app(app)

    admin.add_views(
        TravelerView(Traveler, db.session, category="Users"),
        AdminModelView(Staff, db.session, category="Users"),
        AdminModelView(AdditionRequest, db.session, category="Users"),
    )

    admin.add_views(
        AdminModelView(Route, db.session, category="Route"),
        AdminModelView(Day, db.session, category="Route"),
        AdminModelView(DayVariant, db.session, category="Route"),
        AdminModelView(Segment, db.session, category="Route"),
    )

    admin.add_views(
        AdminModelView(MealPlace, db.session, category="Other"),
        AdminModelView(SimularMealPlaceCache, db.session, category="Other"),
        AdminModelView(POI, db.session, category="Other"),
    )

    admin.add_views(
        AdminModelView(TripInvite, db.session, category="Trip"),
        AdminModelView(TripSession, db.session, category="Trip"),
        AdminModelView(TripParticipant, db.session, category="Trip"),
        AdminModelView(TripVote, db.session, category="Trip"),
    )

    moderator.add_view(
        AssembleRouteView(name="Добавить маршрут на день", endpoint="assemble_route")
    )
