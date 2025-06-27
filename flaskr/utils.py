import datetime


def format_transports(t):
    tickets = t.get("tickets_info")
    places = tickets.get("places") if tickets else []
    m = datetime.timedelta(seconds=int(t.get("duration")))
    formated_transports = {
        "title": t.get("thread").get("title"),
        "transport_type": t.get("thread").get("transport_type"),
        "departure": t.get("departure"),
        "arrival": t.get("arrival"),
        "start_cost_rub": min(places, key=lambda p: p["price"]["whole"])[
            "price"
        ]["whole"]
        if len(places)
        else None,
        "duration_min": m,
    }
    return formated_transports
