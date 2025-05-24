from datetime import datetime
import json
from models import db, Route, TransportOption, Day, DayVariant, Segment, LodgingOption, PriceEntry
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://travel_user:petersburg@localhost:5432/travel_db'
db.init_app(app)


with app.app_context():
    db.drop_all()
    db.create_all()

    with open('plan_travel.json', encoding='UTF-8') as f:
        data = json.load(f)

    for item in data:
        r = Route(
            id=item.get("id") or item["session_id"],
            title=item["title"],
            base_city=item["base_city"],
            duration_days=item["duration_days"],
            estimated_budget_rub=item["estimated_budget_rub"]
        )
        db.session.add(r)

        for opt in item["transport"]["options"]:
            db.session.add(TransportOption(
                route=r,
                mode=opt["mode"],
                there_from=opt["there"]["from"],
                there_to=opt["there"]["to"],
                there_time_min=opt["there"]["time_min"],
                there_cost_rub=opt["there"]["cost_rub"],
                back_from=opt["back"]["from"],
                back_to=opt["back"]["to"],
                back_time_min=opt["back"]["time_min"],
                back_cost_rub=opt["back"]["cost_rub"]
            ))

        for day in item["day_variants"]:
            d = Day(route=r, day_number=day["day"])
            db.session.add(d)
            for var in day["variants"]:
                v = DayVariant(
                    variant_id=var["variant_id"],
                    name=var["name"],
                    est_budget=var["est_budget"],
                    day=d
                )
                db.session.add(v)

                for seg in var["segments"]:
                    s = Segment(variant=v)
                    if "poi" in seg:
                        s.type = "poi"
                        s.poi_name = seg["poi"]["name"]
                        s.must_see = seg["poi"].get("must_see", False)
                        s.arrival_window = seg.get("arrival_window")
                        s.rating = seg.get("rating")
                    elif "meal" in seg:
                        s.type = "meal"
                        s.meal_type = seg["meal"]["type"]
                        s.meal_options_json = json.dumps(seg["meal"]["options"])
                        s.arrival_window = seg.get("time_window")
                    elif "transport_segment" in seg:
                        s.type = "transition"
                        s.walk_time_min = None  # не указывается в исходных данных
                        s.alt_transport_json = json.dumps(seg["transport_segment"]["options"])
                        s.transition_reason = f"{seg['transport_segment']['from']} → {seg['transport_segment']['to']}"
                    elif "transport_back" in seg:
                        s.type = "transition"
                        s.transition_reason = "вернуться назад"
                        s.alt_transport_json = json.dumps([{ "mode": "написано текстом", "note": seg["transport_back"] }])

                    db.session.add(s)

                for lodge in var.get("lodging_options", []):
                    db.session.add(LodgingOption(
                        variant=v,
                        name=lodge["name"],
                        type=lodge["type"]
                    ))
                    db.session.add(PriceEntry(
                        object_type='lodging',
                        object_id=lodge['name'],
                        last_known_price=lodge['avg_price_rub_per_night'],
                        updated_at=datetime.now()
                    ))


    db.session.commit()
