import json
from flask import Blueprint
from config import DevConfig, IS_DEV

mod = Blueprint(
    "assets ",
    __name__,
    static_folder="../static/assets_compiled/bundled",
    static_url_path="/assets/bundled",
)

manifest = {}
if not IS_DEV:
    manifest_path = "flaskr/static/assets_compiled/manifest.json"
    try:
        with open(manifest_path, "r") as content:
            manifest = json.load(content)
    except OSError as exception:
        raise OSError(
            f"Manifest file not found at {manifest_path}. Run `npm run build`."
        ) from exception


@mod.app_context_processor
def add_context():
    def dev_assets(file_path):
        return f"{DevConfig.VITE_DEV_SERVER}/assets/{file_path}"

    def prod_assets(file_path):
        try:
            return f"/assets/{manifest[file_path]['file']}"
        except:
            return "asset-not-found"

    return {"asset": dev_assets if IS_DEV else prod_assets, "is_dev": IS_DEV}
