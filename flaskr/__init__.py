import json
import uuid
from typing import TYPE_CHECKING, Any, Dict, List

import flask_login as login
from flask import Flask, Response, send_from_directory
from flask import session as fk_session
from flask_swagger_ui import get_swaggerui_blueprint
from flask_babel import Babel, format_datetime


from config import SWAGGER_API_URL
from shell import reset_db

from flaskr.constants import ENDPOINTS
from flaskr.db.cities import get_all_cities
from flaskr.db.staff import get_staff

from flaskr.models.models import db
from flaskr.models.user import Traveler

from flaskr.admin import setup_admin
from flaskr.routes.api.meal_places import mod as mealPlacesModule
from flaskr.routes.api.pois import mod as poisModule, limiter
from flaskr.routes.api.routes import mod as routesModule
from flaskr.routes.api.sessions import mod as sessionsModule
from flaskr.routes.views import mod as viewsModule


if TYPE_CHECKING:
    from flaskr.models.city import City


def configure_jinja(app: Flask) -> None:
    app.jinja_env.filters["loads"] = json.loads
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True


babel = Babel()


def create_app(test_config: Dict[str, Any] = {}) -> Flask:
    app = Flask(__name__)
    app.config["BABEL_DEFAULT_LOCALE"] = "ru"
    babel.init_app(app)

    configure_jinja(app)

    if len(test_config) == 0:
        app.config.from_pyfile("flask_config.py", silent=False)
    else:
        app.config.from_mapping(test_config)

    app.register_blueprint(sessionsModule)
    app.register_blueprint(mealPlacesModule)
    app.register_blueprint(routesModule)
    app.register_blueprint(poisModule)
    app.register_blueprint(viewsModule)

    login_manager = login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return get_staff(user_id)

    setup_admin(app)

    limiter.init_app(app)

    swaggerui_blueprint = get_swaggerui_blueprint(
        ENDPOINTS["swwager"],
        SWAGGER_API_URL,
        config={"app_name": "Test application"},
    )

    app.register_blueprint(swaggerui_blueprint)

    app.cli.add_command(reset_db)

    @app.context_processor
    def inject_common_vars() -> Dict[str, List["City"]]:
        return {"cities": get_all_cities()}

    @app.before_request
    def ensure_participant_joined() -> None:
        if fk_session.get("uuid") is None:
            user_uuid = uuid.uuid4()
            fk_session["uuid"] = user_uuid

            user = Traveler(uuid=user_uuid)
            db.session.add(user)
            db.session.commit()

    @app.route("/<path:filename>")
    def static_files(filename: str) -> Response:
        return send_from_directory(app.static_folder, filename)

    return app
