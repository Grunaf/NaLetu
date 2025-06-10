from models import TransportCache
import requests, os
from models import db
import json
import datetime

yandex_api_key = os.getenv("YANDEX_API_KEY")
yandex_api_uri = os.getenv("YANDEX_API_URI")

def search_api_or_get_from_db_transports_from_city_to_city_on_date(date, from_city, to_city):
    cache_duration = datetime.timedelta(minutes=60)
    exist_transport_cache = TransportCache.query.filter_by(date_at=date, start_city_id=from_city.id, end_city_id=to_city.id).first()
    if exist_transport_cache and datetime.datetime.now() - exist_transport_cache.updated_at < cache_duration:
       return exist_transport_cache
    
    params = {"apikey": yandex_api_key,
                "from": from_city.yandex_code,
                "to": to_city.yandex_code,
                "date": date,
                "lang": "ru_RU"}
    
    resp = requests.get(yandex_api_uri, params)
    print(resp.url)
    if resp.status_code == 200:
        transport_data = json.loads(resp.text)
        transport_segments = transport_data.get("segments")
        if exist_transport_cache is None:
            transport_cache = TransportCache(
                start_city_id = from_city.id, 
                end_city_id = to_city.id, 
                data_json = transport_segments,
                date_at = date,
                updated_at = datetime.datetime.now()
            )
            db.session.add(transport_cache)
        else:
            exist_transport_cache.updated_at = datetime.datetime.now()
            exist_transport_cache.data_json = transport_segments

        db.session.commit()
        return transport_cache if exist_transport_cache is None else exist_transport_cache
    