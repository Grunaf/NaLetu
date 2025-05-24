from sklearn.cluster import DBSCAN
import numpy as np
from geopy.distance import geodesic

def adaptive_eps(center_point, poi_point):
    """
    Вычисляет радиус eps для DBSCAN в зависимости от расстояния до центра города.
    """
    distance_km = geodesic(center_point, poi_point).km
    if distance_km < 5:
        return 0.004  # в центре (≈400 м)
    elif distance_km < 15:
        return 0.008  # ближе к окраинам (≈800 м)
    else:
        return 0.015  # далеко (≈1500 м)

def cluster_by_dbscan(geojson_data, city_center, min_samples=2):
    """
    Кластеризация POI с адаптивным радиусом eps.
    geojson_data — исходный GeoJSON,
    city_center — координаты центра города (lat, lon).
    result [lat, lon]
    """

    features = geojson_data["features"]
    valid_pts = []
    valid_features = []
    invalid_count = 0
    invalid_examples = []

    for f in features:
            geom = f.get("geometry", {})
            coords = geom.get("coordinates")
            if (isinstance(coords, list)
                and len(coords) == 2
                and isinstance(coords[0], (int, float))
                and isinstance(coords[1], (int, float))):
                # валидная точка
                valid_pts.append([coords[1], coords[0]])  # [lat, lon]
                valid_features.append(f)
            else:
                invalid_count += 1
                # Соберём пару первых примеров для вывода
                if len(invalid_examples) < 5:
                    invalid_examples.append(coords)

    total = len(features)
    print(f"📝 Всего фичей: {total}, валидных: {len(valid_features)}, отброшено: {invalid_count}")
    if invalid_examples:
        print("⚠️ Примеры отброшенных координат:", invalid_examples)

    if not valid_features:
        print("❌ Нет ни одной валидной точки для кластеризации")
        return {}

    coords = np.array(valid_pts)

    # --- Генерируем индивидуальный eps для каждой точки ---
    eps_values = np.array([
        adaptive_eps(city_center, (lat, lon)) 
        for lat, lon in coords
    ])

    # --- Кластеризация через DBSCAN ---
    # В sklearn DBSCAN принимает только ОДИН eps
    # Поэтому нужно "нормализовать" координаты вручную.
    # Самый простой способ — масштабировать дистанцию.
    # Упрощённо: делим расстояния на eps каждой точки.

    scaled_coords = coords / eps_values[:, np.newaxis]  # растягиваем по каждому объекту

    db = DBSCAN(eps=1.0, min_samples=min_samples).fit(scaled_coords)
    labels = db.labels_

    # --- Формируем кластеры ---
    clusters = {}
    for i, label in enumerate(labels):
        if label == -1:
            continue  # выбросы пропускаем
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(features[i])

    return clusters
