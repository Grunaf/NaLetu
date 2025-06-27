from flask_admin import Admin
from models.meal_place import MealPlace, SimularMealPlaceCache
from models.models import POI, Day, DayVariant, Route, Segment, db
from models.trip import (
    AdditionRequest,
    Staff,
    Traveler,
    TripInvite,
    TripParticipant,
    TripSession,
    TripVote,
)

from app import app
from flaskr.admin.views import (
    AdminModelView,
    AssembleRouteView,
    MyAdminIndexView,
    MyModeratorIndexView,
    TravelerView,
)

admin = Admin(
    app,
    name="Admin-panel",
    index_view=MyAdminIndexView(endpoint="admin", url="/admin"),
    template_mode="bootstrap4",
)
moderator = Admin(
    app,
    name="Operator-panel",
    index_view=MyModeratorIndexView(endpoint="moderator", url="/moderator"),
    template_mode="bootstrap4",
)


admin.add_view(TravelerView(Traveler, db.session, category="Users"))
admin.add_view(AdminModelView(Staff, db.session, category="Users"))
admin.add_view(AdminModelView(AdditionRequest, db.session, category="Users"))

admin.add_view(AdminModelView(Route, db.session, category="Route"))
admin.add_view(AdminModelView(Day, db.session, category="Route"))
admin.add_view(AdminModelView(DayVariant, db.session, category="Route"))
admin.add_view(AdminModelView(Segment, db.session, category="Route"))

admin.add_view(AdminModelView(MealPlace, db.session, category="Other"))
admin.add_view(AdminModelView(SimularMealPlaceCache, db.session, category="Other"))
admin.add_view(AdminModelView(POI, db.session, category="Other"))

admin.add_view(AdminModelView(TripInvite, db.session, category="Trip"))
admin.add_view(AdminModelView(TripSession, db.session, category="Trip"))
admin.add_view(AdminModelView(TripParticipant, db.session, category="Trip"))
admin.add_view(AdminModelView(TripVote, db.session, category="Trip"))


moderator.add_view(
    AssembleRouteView(name="Добавить маршрут на день", endpoint="assemble_route")
)
