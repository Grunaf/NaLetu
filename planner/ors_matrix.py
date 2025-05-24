import openrouteservice
import numpy as np
import os
from dotenv import load_dotenv

from planner.exporter import build_yandex_maps_url

load_dotenv()

ORS_API_KEY = os.getenv("ORS_API_KEY")  # или вставь вручную как строку

client = openrouteservice.Client(key=ORS_API_KEY)



def get_duration_matrix_ors(coords, profile="foot-walking"):
    """
    Получает матрицу времени (в минутах) между координатами через ORS.
    Можно выбрать профиль маршрута: 'foot-walking', 'driving-car', 'driving-hgv', 'cycling-regular' и др.
    """
    if len(coords) < 2:
        return [[0]]
    
    try:
        response = client.distance_matrix(
            locations=coords,
            profile=profile,
            metrics=["duration"],
            units="m",
            resolve_locations=True
        )
        print(f"📡 ORS запрос на {len(coords)} точек")
        print("🚀 ORS получает координаты:")
        for c in coords:
            print(f"{c}")
        print(build_yandex_maps_url(coords));    

        durations = response.get("durations", None)
        if durations is None:
            raise RuntimeError(f"❌ ORS не вернул матрицу продолжительности. Ответ: {response}")
        
        return (np.array(durations) / 60).tolist()  # секунды -> минуты

    except openrouteservice.exceptions.ApiError as e:
        print(f"ORS API error: {e}")
        return None
    
    except Exception as e:
        print(f"❌ Общая ошибка при получении матрицы маршрута: {e}")
        return None
