import datetime
import json

import requests

from config import YA_RASP_API_KEY, YA_RASP_API_URI
from flaskr.models.models import db
from flaskr.models.transport import TransportCache


def get_transports_f_db_or_api(date, from_city, to_city):
    cache_duration = datetime.timedelta(minutes=60)
    exist_transport_cache = TransportCache.query.filter_by(
        date_at=date, start_city_id=from_city.id, end_city_id=to_city.id
    ).first()
    if (
        exist_transport_cache
        and datetime.datetime.now() - exist_transport_cache.updated_at < cache_duration
    ):
        return exist_transport_cache

    params = {
        "apikey": YA_RASP_API_KEY,
        "from": from_city.yandex_code,
        "to": to_city.yandex_code,
        "date": date,
        "lang": "ru_RU",
    }

    resp = requests.get(YA_RASP_API_URI, params)
    if resp.status_code == 200:
        transport_data = resp.json()
        transport_segments = transport_data.get("segments")
        if exist_transport_cache is None:
            transport_cache = TransportCache(
                start_city_id=from_city.id,
                end_city_id=to_city.id,
                data_json=transport_segments,
                date_at=date,
                updated_at=datetime.datetime.now(),
            )
            db.session.add(transport_cache)
        else:
            exist_transport_cache.updated_at = datetime.datetime.now()
            exist_transport_cache.data_json = transport_segments

        db.session.commit()
        return (
            transport_cache if exist_transport_cache is None else exist_transport_cache
        )
    else:
        return resp.status_code, resp.json().get("error").get("text")
