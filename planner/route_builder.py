from datetime import datetime
import hashlib
import json
import random
from geopy.distance import geodesic
from sklearn.cluster import DBSCAN
import numpy as np

from planner.clusterer import cluster_by_dbscan
from planner.exporter import build_yandex_maps_url
from planner.ors_matrix import get_duration_matrix_ors
from planner.user_context import user_sessions, mark_used_clusters
from planner.utils import hash_request, latlon_to_geojson
from planner.cluster_cache import load_cache, save_cache
from planner.loader import load_geojson
from planner.user_context import save_user_sessions

def group_close_pois(points, eps_m=50):
    """
    Группирует близкие POI (например, на площади) в одну "локацию"
    Возвращает список точек, где каждая — основная POI, с вложенными соседями
    """
    if len(points) == 0:
        return []

    coords = np.array([
        [p["geometry"]["coordinates"][1], p["geometry"]["coordinates"][0]] for p in points
    ])

    # Преобразуем eps в градусы (примерно 111_000 м на градус)
    eps_deg = eps_m / 111_000
    model = DBSCAN(eps=eps_deg, min_samples=1).fit(coords)

    grouped_points = []
    labels = model.labels_

    for label in set(labels):
        cluster = [p for i, p in enumerate(points) if labels[i] == label]
        main_poi = cluster[0]
        nearby = [p["properties"].get("name", "Без названия") for p in cluster[1:]]

        if nearby:
            main_poi["properties"]["nearby"] = nearby
        grouped_points.append(main_poi)

    return grouped_points

def calculate_cluster_interest(clusters):
    """
    Подсчёт средней интересности каждой локации (кластера)
    на основе total_interest_score всех точек внутри неё.
    """
    cluster_scores = {}

    for cluster_id, features in clusters.items():
        scores = []
        for feature in features:
            properties = feature.get("properties", {})
            score = properties.get("total_interest_score", 0)
            scores.append(score)
        
        if scores:
            avg_score = sum(scores) / len(scores)
        else:
            avg_score = 0
        
        cluster_scores[cluster_id] = avg_score

    return cluster_scores

def calculate_real_travel_time(user_location, target_location, profile="foot-walking"):
    """
    Реальный расчёт времени в пути через OpenRouteService API.
    Возвращает время в минутах в одну сторону.
    """
    coords = [user_location, target_location]
    matrix = get_duration_matrix_ors(coords, profile)
    if matrix is None:
        print("❌ Ошибка: матрица времени не получена.")
        return float('inf')  # Возвращаем бесконечность, чтобы указать на невозможность расчёта
    
    return matrix[0][1]  # время в пути от user_location до target_location

def build_routes_by_clusters(clusters, cluster_scores, user_location, session, max_minutes_per_day=300, max_clusters_per_day=5, max_days=2, distance_threshold_km=10):
    """
    Построение маршрутов на несколько дней по кластерам, с поддержкой выездных поездок.
    Clusters [lat, lon]
    user_location [lat, lon]
    """
    print("\n🚀 Старт планирования дней по кластерам...")

    # Получаем список исключённых кластеров
    exclude = set(session.get("used_clusters", []))

    # Фильтруем кластеры-кандидаты
    # candidates = [cid for cid in clusters if cid not in exclude]
    # random.shuffle(candidates)

    cluster_centers = {}
    for cluster_id, features in clusters.items():    
        if cluster_id in exclude:
            continue
        coords = np.array([[f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0]] for f in features]) # out [lat, lon]
        center_lat = np.mean(coords[:, 0])
        center_lon = np.mean(coords[:, 1])
        cluster_centers[cluster_id] = (center_lat, center_lon)

    unvisited = set(cluster_centers.keys())
    all_days_routes = []
    day_counter = 1

    while unvisited and day_counter <= max_days:
        current_location = user_location
        visited_today = []
        total_time_today = 0
        
        # Сперва ищем выездной кластер
        distant_clusters = [
            cid for cid in unvisited
            if geodesic(current_location, cluster_centers[cid]).km > distance_threshold_km
        ]

        if distant_clusters:
            # Если есть дальние кластеры — выберем самый интересный
            distant_clusters = sorted(
                distant_clusters,
                key=lambda cid: cluster_scores.get(cid, 0),
                reverse=True
            )
            selected_cluster = distant_clusters[0]
            coord_from = latlon_to_geojson(user_location)
            coord_to = latlon_to_geojson(cluster_centers[selected_cluster])

            travel_time_one_way = calculate_real_travel_time(coord_from, coord_to, profile="driving-car")
            full_travel_time = travel_time_one_way * 2  # туда-обратно

            if full_travel_time + 120 <= max_minutes_per_day:  # 2 часа запаса на прогулку
                visited_today = [selected_cluster]
                total_time_today = full_travel_time
                unvisited.remove(selected_cluster)

                print(f"🚗 День {day_counter}: выбрана выездная поездка на кластер {selected_cluster}")
                print(f"   Время на дорогу туда-обратно: {int(full_travel_time)} минут")
                print(f"   Оценка интересности: {cluster_scores.get(selected_cluster, 0)}")

                all_days_routes.append({
                    "day": day_counter,
                    "clusters": visited_today,
                    "total_estimated_time_min": int(total_time_today),
                    "note": f"Выездная поездка: дорога туда-обратно займет {int(full_travel_time)} минут",
                    "is_remote_cluster": True  # Добавляем флаг
                })

                day_counter += 1
                continue
            else:
                # ❗ если поездка на выездной кластер невозможна — тоже убираем
                print(f"❌ Выездной кластер {selected_cluster} слишком далеко, пропускаем")
                unvisited.remove(selected_cluster)


        # Обычная логика для ближних кластеров
        while unvisited and len(visited_today) < max_clusters_per_day:
            nearest_cluster = min(
                unvisited,
                key=lambda cid: geodesic(current_location, cluster_centers[cid]).km - 0.05 * cluster_scores.get(cid, 0)
            )

            distance_km = geodesic(current_location, cluster_centers[nearest_cluster]).km
            estimated_travel_time_min = (distance_km / 5.0) * 60  # пешком
            estimated_visit_time_min = 60  # базовое среднее время на локацию

            estimated_total_time = estimated_travel_time_min + estimated_visit_time_min

            if total_time_today + estimated_total_time > max_minutes_per_day:
                break

            visited_today.append(nearest_cluster)
            unvisited.remove(nearest_cluster)
            total_time_today += estimated_total_time
            current_location = cluster_centers[nearest_cluster]
            print(f"🗺 Добавляем кластер {nearest_cluster} на день {day_counter}")
            print(f"   Расстояние: {distance_km:.2f} км, примерное время в пути: {estimated_travel_time_min:.1f} мин")
            print(f"   Оценка интересности: {cluster_scores.get(nearest_cluster, 0)}")

        if visited_today:
            all_days_routes.append({
                "day": day_counter,
                "clusters": visited_today,
                "total_estimated_time_min": int(total_time_today)
            })
            print(f"✅ День {day_counter} сформирован: {len(visited_today)} кластеров, общее время {total_time_today:.1f} минут\n")

            day_counter += 1
            if max_days is not None and day_counter > max_days:
                print(f"📅 Достигнут лимит по дням: {max_days} дней")
                break
    used = set()
    for day_route in all_days_routes:
        used.update(day_route.get("clusters", []))
    # Помечаем использованные кластеры
    session["used_clusters"] = list(exclude.union(used))
    # 3) Сохраняем сессию (если у вас есть функция save_user_sessions)
    save_user_sessions()
    return all_days_routes


def build_day_route_from_clusters(clusters, selected_cluster_ids, user_location, max_minutes=300, max_poi_per_day=15, is_remote_cluster=False):
    """
    Строит маршрут на один день по выбранным кластерам,
    начиная от локации пользователя, фильтруя самые интересные точки
    и учитывая лимит времени.
    """
    print(f"\n📅 Построение маршрута на один день по {len(selected_cluster_ids)} кластерам...")

    points = []

    for cluster_id in selected_cluster_ids:
        points.extend(clusters.get(cluster_id, []))

    if not points:
        return {
            "total_estimated_time_min": 0,
            "points": [],
            "yandex_url": build_yandex_maps_url([user_location]),
            "note": "Нет точек для маршрута"
        }

    # Добавляем визитное время к каждой точке
    for point in points:
        point["visit_time"] = point.get("properties", {}).get("estimated_time", 30)

    # Фильтрация по интересности
    points = sorted(
        points,
        key=lambda p: p.get("properties", {}).get("total_interest_score", 0),
        reverse=True
    )
    points = points[:max_poi_per_day]  # Ограничение на количество точек

    # Добавляем дом в начало маршрута
    fake_home = {
        "geometry": {"coordinates": latlon_to_geojson(user_location)},
        "properties": {"name": "Дом"},
        "visit_time": 0
    }
    points = [fake_home] + points

    coords = [p["geometry"]["coordinates"] for p in points]

    if len(coords) < 2:
        return {
            "total_estimated_time_min": 0,
            "points": [],
            "yandex_url": build_yandex_maps_url([user_location]),
            "note": "Недостаточно точек для построения маршрута"
        }
    if is_remote_cluster:
        # Получаем матрицу продолжительности переходов между точками
        matrix = get_duration_matrix_ors(coords, profile="driving-car")
    else:
        # Получаем матрицу продолжительности переходов между точками
        matrix = get_duration_matrix_ors(coords)

    visited = set()
    current_index = 0  # стартуем из дома
    total_time = 0
    route = []

    while True:
        best_idx = None
        best_score = float("inf")

        for i in range(1, len(points)):
            if i in visited:
                continue

            walk_time = matrix[current_index][i]
            interest_score = points[i].get("properties", {}).get("total_interest_score", 0)
            visit_time = points[i]["visit_time"]
            # Баланс времени перехода + интересности
            total = walk_time + visit_time - 0.1 * interest_score  # Чем выше интересность, тем привлекательнее точка

            if total < best_score:
                best_score = total
                best_idx = i

            print(f"➡️ Переход от точки {current_index} к точке {best_idx}:")
            print(f"   Время на переход: {walk_time:.1f} мин, интересность точки: {interest_score}")
            print(f"   Суммарное время: {total_time:.1f} мин")

        if best_idx is None or total_time + (matrix[current_index][best_idx] + points[best_idx]["visit_time"]) > max_minutes:
            break

        total_time += matrix[current_index][best_idx] + points[best_idx]["visit_time"]
        visited.add(best_idx)
        route.append(points[best_idx])
        current_index = best_idx
        print(f"✅ Маршрут на день построен: {len(route)} точек, общее время {total_time:.1f} минут\n")
    

    coords_for_map = [fake_home["geometry"]["coordinates"]] + [p["geometry"]["coordinates"] for p in route]
    yandex_url = build_yandex_maps_url(coords_for_map)

    return {
        "total_estimated_time_min": int(total_time),
        "points": [
            {
                "name": p["properties"].get("name"),
                "coordinates": p["geometry"]["coordinates"],
                "estimated_time": p["visit_time"]
            } for p in route
        ],
        "yandex_url": yandex_url
    }

def build_routes_for_all_days(user_location, max_minutes_per_day=300, max_days=2, user_id=None):
    """
    Основная функция: строит маршруты на все дни по локациям,
    используя кластеризацию, интересность и ограничение времени.
    user_location [lat, lon]
    """

    print(f"\n=== Начинаем построение маршрутов для пользователя {user_id} ===")
    print(f"Городской центр: {user_location}")

    geojson_data = load_geojson("with_popularity_(MAqZGVA)(Peter)v2.geojson")

    # 1) Получим хеш входного geojson:
    raw = json.dumps(geojson_data, sort_keys=True, ensure_ascii=False)
    geo_hash = hashlib.sha256(raw.encode()).hexdigest()
    city_center = (59.9386, 30.3141)  # Санкт-Петербург, можно параметризовать [lat, lon]

    # 2) Загрузим кэш
    cache = load_cache()
    if cache.get("hash") == geo_hash:
        print("✅ Кластеризация: берем из кэша")
        clusters = cache["clusters"]
    else:
        print("🚀 Кластеризация: пересчитываем и сохраняем в кэш")
        clusters = cluster_by_dbscan(geojson_data, city_center)
        cache["hash"] = geo_hash
        cache["clusters"] = clusters
        save_cache(cache)

    clusters = cluster_by_dbscan(geojson_data, city_center)
    cluster_scores = calculate_cluster_interest(clusters)

    print(f"✅ Сформировано {len(clusters)} локаций.")

    session = user_sessions.setdefault(str(user_id), {})
    excluded_names = session.get("exclude_names", [])
    excluded_categories = session.get("exclude_categories", [])
    print(f"Фильтры: категории - {excluded_categories}, названия - {excluded_names}")

    request_data = {
        "location": user_location,
        "excluded": {
            "names": excluded_names,
            "categories": excluded_categories
        }
    }

    request_hash = hash_request(request_data)
    # if session.get("last_request_hash") == request_hash:
    #     print("✅ Используем кэш")
    #     return session.get("cached_routes")

    day_cluster_routes = build_routes_by_clusters(
        clusters=clusters,
        cluster_scores=cluster_scores,
        user_location=user_location,
        session=session,
        max_minutes_per_day=max_minutes_per_day,
        max_clusters_per_day=5,
        max_days=max_days
    )

    all_routes = []

    for day_route in day_cluster_routes:
        day = day_route["day"]
        selected_clusters = day_route["clusters"]

        day_plan = build_day_route_from_clusters(
            clusters=clusters,
            selected_cluster_ids=selected_clusters,
            user_location=user_location,
            max_minutes=max_minutes_per_day,
            is_remote_cluster=day_route.get("is_remote_cluster", False),  # Используем флаг
        )

        all_routes.append({
            "day": day,
            "total_estimated_time_min": day_plan["total_estimated_time_min"],
            "points": day_plan["points"],
            "yandex_url": day_plan["yandex_url"]
        })

    all_used = [int(cid) for day in day_cluster_routes for cid in day["clusters"]]
    mark_used_clusters(user_id, all_used)

    # Save the planned routes and previous trips in the session
    session["last_request_hash"] = request_hash
    session["cached_routes"] = all_routes

    # Store previous trips
    previous_trips = session.get("previous_trips", [])
    previous_trips.append({
        "date": str(datetime.now()),  # Store the date of the trip
        "routes": all_routes
    })
    session["previous_trips"] = previous_trips

    user_sessions[str(user_id)] = session
    save_user_sessions()

    return all_routes
