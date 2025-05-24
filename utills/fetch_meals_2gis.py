
import requests
import os

DGIS_API_KEY = os.getenv("DGIS_API_KEY")

def fetch_meals_2gis(lat, lon, radius=700, limit=5):
    url = "https://catalog.api.2gis.com/3.0/items"
    params = {
        "key": DGIS_API_KEY,
        "lat": lat,
        "lon": lon,
        "radius": radius,
        "q": "кафе ресторан",
        "type": "branch",
        "fields": "items.rubrics,items.schedule,items.ratings,items.avg_bill,items.links",
        "page_size": limit
    }

    res = requests.get(url, params=params)
    res.raise_for_status()
    items = res.json()["result"]["items"]

    results = []
    for item in items:
        try:
            name = item["name"]
            latlon = item["point"]
            coords = f"{latlon['lat']},{latlon['lon']}"
            cuisine = ", ".join(r.get("name", "") for r in item.get("rubrics", []) if "кафе" in r.get("name", "").lower() or "ресторан" in r.get("name", "").lower())
            avg_check = item.get("avg_bill", {}).get("value")
            schedule = item.get("schedule", {}).get("working_hours")
            rating = item.get("rating", {}).get("value")
            website = item.get("links", {}).get("website")

            results.append({
                "name": name,
                "coords": coords,
                "cuisine": cuisine or None,
                "avg_check_rub": int(avg_check) if avg_check else None,
                "opening_hours": schedule,
                "rating": float(rating) if rating else None,
                "website": website
            })
        except Exception as e:
            print("⚠️ Ошибка при разборе заведения:", e)

    return results
