import json

def load_geojson(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
