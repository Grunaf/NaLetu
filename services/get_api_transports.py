from models import TransportOption
import requests, os

yandex_api_key = os.getenv("YANDEX_API_KEY")
yandex_api_uri = os.getenv("YANDEX_API_URI")

def get_transports(date, from_code_station, to_code_station):
    params = {"apikey": yandex_api_key,
                "from": from_code_station,
                "to": to_code_station,
                "lang": "ru_RU"}
    resp = requests.get(yandex_api_uri, params)
    if resp.status_code == 200:
        print()
        