import os

SECRET_KEY = os.getenv("SECRET_KEY")

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_API_URI = os.getenv("YANDEX_API_URI")
DGIS_API_KEY = os.getenv("DGIS_API_KEY")
DGIS_API_URI = os.getenv("DGIS_API_URI")
YA_MAP_API_KEY = os.getenv("YA_MAP_API_KEY")

TRAVEL_PAY_HOTEL_API_KEY = os.getenv("TRAVEL_PAY_HOTEL_API_KEY")
LOOKUP_URL = "https://engine.hotellook.com/api/v2/lookup.json"
CACHE_URL = "https://engine.hotellook.com/api/v2/cache.json"
