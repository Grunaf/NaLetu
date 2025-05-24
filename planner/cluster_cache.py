import json
import os
from planner.utils import hash_request  # или своя функция hash_geojson(data)

CACHE_FILE = "planner/cluster_cache.json"

def load_cache():
    raw = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    # Преобразуем ключи обратно в int
    if "clusters" in raw:
        c = raw["clusters"]
        raw["clusters"] = { int(k): v for k,v in c.items() }
    return raw

def save_cache(cache: dict):
    # Преобразуем ключи clusters в str
    if "clusters" in cache:
        raw = cache["clusters"]
        cache["clusters"] = { str(k): v for k,v in raw.items() }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

