import json
import uuid
from typing import Any, Dict, List

from flask import (
    Flask,
    Response,
    send_from_directory,
)
from flask import session as fk_session

from flaskr.db.cities import get_all_cities
from flaskr.models.city import City
from flaskr.models.models import db
from flaskr.models.user import User
from flaskr.routes.api.meal_places import mod as mealPlacesModule
from flaskr.routes.api.sessions import mod as sessionsModule
from flaskr.routes.views import mod as viewsModule
# from shell import mod as shellModule
from shell import reset_db


def configure_jinja(app: Flask) -> None:
    app.jinja_env.filters["loads"] = json.loads
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True


def create_app(test_config: Dict[str, Any] = {}) -> Flask:
    app = Flask(__name__)
    configure_jinja(app)

    if len(test_config) == 0:
        app.config.from_pyfile("flask_config.py", silent=False)
    else:
        app.config.from_mapping(test_config)

    app.register_blueprint(sessionsModule)
    app.register_blueprint(mealPlacesModule)
    app.register_blueprint(viewsModule)
    # app.register_blueprint(shellModule)
    app.cli.add_command(reset_db)

    @app.context_processor
    def inject_common_vars() -> Dict[str, List[City]]:
        return {"cities": get_all_cities()}

    @app.before_request
    def ensure_participant_joined() -> None:
        if fk_session.get("uuid") is None:
            user_uuid = uuid.uuid4()
            fk_session["uuid"] = user_uuid

            user = User(uuid=user_uuid)
            db.session.add(user)
            db.session.commit()

    @app.route("/<path:filename>")
    def static_files(filename: str) -> Response:
        return send_from_directory(app.static_folder, filename)


    return app
