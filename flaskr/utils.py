import datetime

import flask_babel


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


def format_transports(t):
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

    return {
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
