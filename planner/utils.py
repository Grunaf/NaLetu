import hashlib
import json

def hash_request(data):
    json_data = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_data.encode()).hexdigest()

def geojson_to_latlon(geojson_coord):
    """
    Преобразует координату из GeoJSON ([lon, lat]) в стандартный вид (lat, lon)
    для расчётов расстояний через geopy.
    """
    lon, lat = geojson_coord
    return (lat, lon)

def latlon_to_geojson(coord):
    """
    Преобразует координату из (lat, lon) обратно в GeoJSON формат [lon, lat]
    для сохранения в файлы или отправки в API типа ORS.
    """
    return [coord[1], coord[0]]  # [lon, lat]

