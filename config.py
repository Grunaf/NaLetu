import os

SECRET_KEY = os.getenv("SECRET_KEY")

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

YA_RASP_API_KEY = os.getenv("YA_RASP_API_KEY")
YA_RASP_API_URI = os.getenv("YA_RASP_API_URI")
YA_MAP_API_KEY = os.getenv("YA_MAP_API_KEY")

DGIS_API_KEY = os.getenv("DGIS_API_KEY")
DGIS_API_URI = os.getenv("DGIS_API_URI")
DGIS_API_URI_ITEMS = DGIS_API_URI + "items"
DGIS_API_URI_HINT = DGIS_API_URI + "suggests"
DGIS_API_URI_GET_BY_ID = DGIS_API_URI_ITEMS + "/byid"

TRAVEL_PAY_HOTEL_API_KEY = os.getenv("TRAVEL_PAY_HOTEL_API_KEY")
LOOKUP_URL = "https://engine.hotellook.com/api/v2/lookup.json"
CACHE_URL = "https://engine.hotellook.com/api/v2/cache.json"

SWAGGER_API_URL = os.getenv("SWAGGER_API_URL")
