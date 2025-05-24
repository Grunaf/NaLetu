import json

def export_route_json(route, filename="day1.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(route, f, indent=2, ensure_ascii=False)


def export_geojson(route, filename="day1.geojson"):
    coords = [p["coordinates"] for p in route["points"]]

    geojson_output = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": p["coordinates"]},
                "properties": {"name": p["name"], "estimated_time": p["estimated_time"]}
            } for p in route["points"]
        ] + [
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {"type": "route", "day": route["date"]}
            }
        ]
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(geojson_output, f, indent=2, ensure_ascii=False)

def build_yandex_maps_url(route_points: list[list[float]]) -> str:
    """
    Принимает список точек маршрута [lon, lat] и возвращает ссылку на Яндекс.Карты с маршрутом.
    """
    if not route_points:
        return "Нет точек для построения маршрута."

    # Переводим в формат lat,lon и собираем через ~
    rtext = "~".join([f"{lat},{lon}" for lon, lat in route_points])

    # Примерно центр карты на первой точке
    center = f"{route_points[0][0]},{route_points[0][1]}"
    
    return f"https://yandex.ru/maps/2/saint-petersburg/?ll={center}&mode=routes&rtext={rtext}&rtt=pd"
