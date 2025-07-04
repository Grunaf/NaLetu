import os

ENV = os.getenv("FLASK_ENV", "dev")


class Config:
    DB_USER = os.getenv("POSTGRES_USER")
    DB_PASS = os.getenv("POSTGRES_PASSWORD")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT")
    DB_NAME = os.getenv("POSTGRES_DB")

    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

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
    SENTRY_DSN = os.getenv("SENTRY_DSN")

    DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE")


class DevConfig(Config):
    DEBUG = True
    TESTING = True


class ProdConfig(Config):
    DEBUG = False
    TESTING = False
