import json
import os
import uuid
from typing import Any, Dict

import flask_login as login
from flask import Flask, Response, render_template, send_from_directory
from flask import session as fk_session
from flask_swagger_ui import get_swaggerui_blueprint
from flask_babel import Babel

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from config import Config
from flaskr.db.travelers import create_traveler_db
from flaskr.jinja_filters import setup_filters
from shell import reset_db

from flaskr.constants import ENDPOINTS
from flaskr.db.cities import get_all_cities
from flaskr.db.staff import get_staff

from flaskr.schemas.city import City as CityRead

from flaskr.admin import setup_admin
from flaskr.routes.api.meal_places import mod as mealPlacesModule
from flaskr.routes.api.pois import mod as poisModule, limiter
from flaskr.routes.api.routes import mod as routesModule
from flaskr.routes.api.sessions import mod as sessionsModule
from flaskr.routes.views import mod as viewsModule

DEFAULT_TIMEZONE = Config.DEFAULT_TIMEZONE
SWAGGER_API_URL = Config.SWAGGER_API_URL
SENTRY_DSN = Config.SENTRY_DSN


def configure_jinja(app: Flask) -> None:
    app.jinja_env.filters["loads"] = json.loads
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True


babel = Babel()


def configure_app(app, test_config):
    if len(test_config) == 0:
        env = os.getenv("FLASK_ENV", "dev")
        if env == "prod":
            app.config.from_object("config.ProdConfig")
        else:
            app.config.from_object("config.DevConfig")
    else:
        app.config.from_mapping(test_config)


def create_app(test_config: Dict[str, Any] = {}) -> Flask:
    app = Flask(__name__)
    app.config["BABEL_DEFAULT_LOCALE"] = "ru"
    babel.init_app(app, default_timezone=DEFAULT_TIMEZONE)

    configure_jinja(app)
    configure_app(app, test_config)

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
    setup_filters(app)

    limiter.init_app(app)

    swaggerui_blueprint = get_swaggerui_blueprint(
        ENDPOINTS["swwager"],
        SWAGGER_API_URL,
        config={"app_name": "Test application"},
    )
    sentry_sdk.init(SENTRY_DSN, integrations=[FlaskIntegration()])

    app.register_blueprint(swaggerui_blueprint)

    app.cli.add_command(reset_db)

    @app.context_processor
    def inject_common_vars() -> Dict[str, Any]:
        user_city = (
            CityRead.model_validate(fk_session.get("user_city")).model_dump()
            if fk_session.get("user_city")
            else None
        )
        return {"cities": get_all_cities(), "user_city": user_city}

    @app.before_request
    def ensure_participant_joined() -> None:
        if fk_session.get("uuid") is None:
            user_uuid = uuid.uuid4()
            fk_session["uuid"] = str(user_uuid)

            create_traveler_db(user_uuid)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        sentry_sdk.capture_event(e)
        return render_template("errors/500.html"), 500

    @app.errorhandler(403)
    def not_accesed(e):
        return render_template("errors/403.html"), 403

    @app.route("/<path:filename>")
    def static_files(filename: str) -> Response:
        return send_from_directory(app.static_folder, filename)

    return app
