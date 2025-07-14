import datetime
import math

from urllib.parse import urlencode

from config import Config


def human_readeble_duration(duration: datetime.timedelta):
    total_minutes = int(duration.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60

    parts = []
    if hours:
        parts.append(f"{hours} ч.")
    if minutes:
        parts.append(f"{minutes} мин.")
    return " ".join(parts) or "0 м."


def format_transports(t, from_city_slug, to_city_slug):
    tickets = t.get("tickets_info")
    places = tickets.get("places") if tickets else []
    thread = t.get("thread")

    from_data = t.get("from")
    from_title = (
        from_data.get("popular_title")
        if from_data.get("popular_title")
        else from_data.get("title")
    )

    to_data = t.get("to")
    to_title = (
        to_data.get("popular_title")
        if to_data.get("popular_title")
        else to_data.get("title")
    )

    duration_delta = datetime.timedelta(seconds=int(t.get("duration")))
    formatted_duration = human_readeble_duration(duration_delta)
    start_cost_rub = (
        min(places, key=lambda p: p["price"]["whole"])["price"]["whole"]
        if len(places)
        else None
    )
    departure = datetime.datetime.fromisoformat(t.get("departure"))
    arrival = datetime.datetime.fromisoformat(t.get("arrival"))

    data = {
        "uid": thread.get("uid"),
        "carrier": thread.get("carrier"),
        "number": thread.get("number"),
        "title": thread.get("title"),
        "from_title": from_title,
        "to_title": to_title,
        "transport_type": thread.get("transport_type"),
        "departure": departure,
        "arrival": arrival,
        "start_cost_rub": start_cost_rub,
        "duration": formatted_duration,
    }

    # NOTE: Tutu redirect currently inactive
    # Waiting for partnership integration
    # URL logic and parameters to be updated when partner links are available
    if Config.ENABLE_TUTU_REDIRECT:
        base_url = f"{Config.TUTU_SEARCH_URI}/{from_city_slug}/{to_city_slug}"
        params = {"class": "Y", "travelers": "1"}
        query = urlencode(params)
        buy_page = f"{base_url}/{query}"

        data["buy_page"] = buy_page

    return data


def meters_to_degrees(meters: float, latitude_deg: float) -> tuple[float, float]:
    meters_per_deg_lat = 111320.0
    meters_per_deg_lon = 40075000 * math.cos(math.radians(latitude_deg)) / 360

    deg_lat = meters / meters_per_deg_lat
    deg_log = meters / meters_per_deg_lon
    return deg_lat, deg_log
