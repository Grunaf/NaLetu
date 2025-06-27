from urllib.parse import unquote

from flask import Blueprint, abort, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app import app
from flaskr.services.get_f_api_poi import (
    create_or_get_poi,
    fetch_poi_from_dgis,
    get_hints_object,
    parse_poi_data,
)

limiter = Limiter(get_remote_address, app=app)

mod = Blueprint("api/poi", __name__, url_prefix="/api/poi")


@app.route("/hints")
@limiter.limit("10 per minute")
def get_poi_hints():
    object_name = unquote(request.args.get("q"))
    location = unquote(request.args.get("location"))
    hints_object, error_code = get_hints_object(object_name, location)

    if error_code == 400:
        return jsonify({"error": "Метод на найден"}), 400
    if error_code == 404:
        return jsonify({"error": "Ничего не найдено"}), 404
    if error_code is not None:
        return jsonify({"error": "Непредвиденная ошибка"}), error_code

    return jsonify(hints_object)


@app.route("/create_or_get", methods=["POST"])
def create_poi_by_dgis_id():
    data = request.json or {}
    dgis_id = data.get("dgis_id")

    if dgis_id is None:
        abort(400, "Не указан dgis_id точки")

    data = fetch_poi_from_dgis(dgis_id)
    poi_dgis = parse_poi_data(data, dgis_id)
    poi = create_or_get_poi(poi_dgis)
    return jsonify({"id": poi.id})
