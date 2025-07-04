import datetime

import requests
from sentry_sdk import logger as sentry_logger

from config import Config
from flaskr.db.transports import create_transport_cache, get_transport_cache
from flaskr.models.cities import City
from flaskr.models.models import db
from flaskr.models.transport import TransportCache

YA_RASP_API_KEY = Config.YA_RASP_API_KEY
YA_RASP_API_URI = Config.YA_RASP_API_URI


def fetch_transport_from_api(
    date: datetime.date, from_ya_code: str, to_ya_code: str
) -> requests.Response:
    params = {
        "apikey": YA_RASP_API_KEY,
        "from": from_ya_code,
        "to": to_ya_code,
        "date": date,
        "lang": "ru_RU",
    }

    return requests.get(YA_RASP_API_URI, params)


def get_transports(
    date: datetime.date, from_city: City, to_city: City
) -> TransportCache | None:
    cache_duration = datetime.timedelta(minutes=60)
    exist_transport_cache = get_transport_cache(date, from_city.id, to_city.id)
    if (
        exist_transport_cache
        and datetime.datetime.now() - exist_transport_cache.updated_at < cache_duration
    ):
        return exist_transport_cache

    resp = fetch_transport_from_api(date, from_city.yandex_code, to_city.yandex_code)
    if resp.status_code != 200:
        data = resp.json()
        sentry_logger.error(data["error"]["text"])
        return None

    transport_data = resp.json()
    transport_segments = transport_data.get("segments")
    if exist_transport_cache is None:
        transport_cache = create_transport_cache(
            date, from_city.id, to_city.id, transport_segments
        )
        return transport_cache
    else:
        exist_transport_cache.updated_at = datetime.datetime.now()
        exist_transport_cache.data_json = transport_segments
        db.session.commit()
        return exist_transport_cache
