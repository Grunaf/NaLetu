# 🧭 Налету

Сервис для планирования коротких поездок по городам.  
Позволяет быстро подобрать маршрут, транспорт, места для еды и рассчитать примерную стоимость поездки.  
Поддерживает групповой выбор маршрутов.

---
## 🗂️ Данные для работы проекта

Проект использует базу данных с маршрутами, достопримечательностями, кафе и т.д.  
Для полноценной демонстрации требуется большой объём данных, который **пока не включён в репозиторий**.

Во время разработки использовался тестовый `seed`-файл, однако:
- данные неполные и частично некорректные;
- они не отражают реальную работу проекта;
- поэтому **он не включён в публичную версию**.

---
## 🚀 Запуск проекта

### 1. Клонировать репозиторий
```bash
git clone https://github.com/Grunaf/NaLetu.git
cd NaLetu
```

### 2. Создать .env файл
Создайте файл .env в корне проекта и заполните нужные переменные:
```
    POSTGRES_USER = YOUR_TRAVELER
    POSTGRES_PASSWORD = YOUR_PASSWORD
    POSTGRES_HOST = localhost
    POSTGRES_PORT = 5432
    POSTGRES_DB = YOUR_DB

    SECRET_KEY = YOUR_SECRET_KEY

    YA_RASP_API_KEY = YOUR_API
    YA_RASP_API_URI = https://api.rasp.yandex-net.ru/v3.0/search/
    YA_MAP_API_KEY = YOUR_API

    DGIS_API_KEY = YOUR_API
    DGIS_API_URI = "https://catalog.api.2gis.com/3.0/"
    DGIS_API_URI_ITEMS = DGIS_API_URI + "items"
    DGIS_API_URI_HINT = DGIS_API_URI + "suggests"
    DGIS_API_URI_GET_BY_ID = DGIS_API_URI_ITEMS + "/byid"

    TUTU_SEARCH_URI = TUTU_SEARCH_URI
    ENABLE_TUTU_REDIRECT = False

    TRAVEL_PAY_HOTEL_API_KEY = TRAVEL_PAY_HOTEL_API_KEY
    LOOKUP_URL = https://engine.hotellook.com/api/v2/lookup.json
    CACHE_URL = https://engine.hotellook.com/api/v2/cache.json

    SWAGGER_API_URL = SWAGGER_API_URL
    SENTRY_DSN = YOUR_SENTRY_DNS

    DEFAULT_TIMEZONE = DEFAULT_TIMEZONE

    DEFAULT_CITY_SLUG = YOUR_CITY_SLUG
```

### 3. Собрать и запустить контейнеры
```
docker compose up --build
```

### 4. Применить миграции
```
docker compose exec app python manage.py migrate
```
