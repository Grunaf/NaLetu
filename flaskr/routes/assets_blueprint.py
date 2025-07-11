from flask import Blueprint
from config import DevConfig, IS_DEV

mod = Blueprint("assets ", __name__, static_url_path="/asses")


@mod.app_context_processor
def add_context():
    def dev_assets(filepath):
        return f"{DevConfig.VITE_DEV_SERVER}/flaskr/static/{filepath}"

    def prod_assets():
        pass

    return {"asset": dev_assets if IS_DEV else prod_assets, "is_dev": IS_DEV}
