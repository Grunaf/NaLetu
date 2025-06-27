import json
import os

import flask_login as login
from flask_admin import Admin
from flask_migrate import Migrate, downgrade, upgrade
from flask_swagger_ui import get_swaggerui_blueprint
from sqlalchemy import select, text

from flaskr import create_app
from flaskr.admin.views import (
    AdminModelView,
    AssembleRouteView,
    MyAdminIndexView,
    MyModeratorIndexView,
    TravelerView,
)
from models.meal_place import MealPlace, SimularMealPlaceCache
from models.models import POI, Day, DayVariant, PriceEntry, Route, Segment, db
from models.trip import (
    AdditionRequest,
    Staff,
    Traveler,
    TripInvite,
    TripParticipant,
    TripSession,
    TripVote,
)
from routes.hotels import hotels_bp

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# app = Flask(__name__, static_folder='static')
# app.jinja_env.filters['loads'] = json.loads
# app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app = create_app()
db.init_app(app)
SWAGGER_URL = "/api/docs"  # URL for exposing Swagger UI (without trailing '/')
API_URL = "http://petstore.swagger.io/v2/swagger.json"  # Our API url (can of course be a local resource)
app.register_blueprint(hotels_bp)

migrate = Migrate(app, db)
PORT = 3000

MEAL_TYPE = 0
POI_TYPE = 1

SEGMENT_TYPE = {MEAL_TYPE: "meal", POI_TYPE: "poi"}

# ====================
# UTILS
# ====================


def get_price(object_type, object_id):
    p = PriceEntry.query.filter_by(object_type=object_type, object_id=object_id).first()
    return p.last_known_price if p else None


def extract_entry_point_summary(entry_json_str):
    if not entry_json_str:
        return "–"
    try:
        data = json.loads(entry_json_str)
        from_point = data.get("from_point", {}).get("name")
        zones = data.get("recommendations", [])
        if from_point:
            return f"от {from_point} / {len(zones)} зон"
        return f"{len(zones)} зон входа"
    except Exception:
        return "–"


def seed_db(file_seed="initial_data.sql"):
    with app.app_context():
        db.create_all()
        with open(file_seed, encoding="UTF-8") as file:
            db.session.execute(text(file.read()))
        db.session.commit()


@app.cli.command("reset-db")
def reset_db():
    print("Dropping all tables")
    downgrade(revision="base")
    print("Upgrading")
    upgrade()
    print("Seeding")
    seed_db()


def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        stmt = select(Staff).where(Staff.uuid == user_id)
        return db.session.execute(stmt).scalars().first()


init_login()

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
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "Test application"}
)

app.register_blueprint(swaggerui_blueprint)


if __name__ == "__main__":
    app.run(debug=True, port=PORT)
