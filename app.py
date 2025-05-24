from flask import Flask, jsonify, request, send_from_directory, abort
from flask_migrate import Migrate
from models import db, Route, TransportOption, Day, DayVariant, Segment, LodgingOption, PriceEntry
from datetime import datetime
import json
import os

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
db.init_app(app)

# После app.config и db.init_app(app)
migrate = Migrate(app, db)

PORT = 3000

# ====================
# UTILS
# ====================

def get_price(object_type, object_id):
    p = PriceEntry.query.filter_by(object_type=object_type, object_id=object_id).first()
    return p.last_known_price if p else None
    
def extract_entry_point_summary(entry_json_str):
    if not entry_json_str:
        return "–"
    try:
        data = json.loads(entry_json_str)
        from_point = data.get("from_point", {}).get("name")
        zones = data.get("recommendations", [])
        if from_point:
            return f"от {from_point} / {len(zones)} зон"
        return f"{len(zones)} зон входа"
    except Exception:
        return "–"

# ====================
# ROUTES
# ====================

@app.route('/api/routes')
def get_routes():
    routes = Route.query.all()
    return jsonify([
        {
            "id": r.id,
            "title": r.title,
            "days": r.duration_days,
            "entry_point": extract_entry_point_summary(r.entry_info_json),
            "budget": r.estimated_budget_rub,
            "description": r.title,
            "img": r.img,
            "entry_info_available": bool(r.entry_info_json)

        } for r in routes
    ])

@app.route('/api/plan/<route_id>')
def get_plan(route_id):
    route = Route.query.get(route_id)
    if not route:
        return abort(404)

    return jsonify({
        "id": route.id,
        "title": route.title,
        "entry_info": json.loads(route.entry_info_json) if route.entry_info_json else None,
        "duration_days": route.duration_days,
        "estimated_budget_rub": route.estimated_budget_rub,
        "transport": {
            "options": [
                {
                    "mode": t.mode,
                    "there": {
                        "from": t.there_from,
                        "to": t.there_to,
                        "time_min": t.there_time_min,
                        "cost_rub": t.there_cost_rub
                    },
                    "back": {
                        "from": t.back_from,
                        "to": t.back_to,
                        "time_min": t.back_time_min,
                        "cost_rub": t.back_cost_rub
                    }
                } for t in route.transports
            ]
        },
        "day_variants": [
            {
                "day": day.day_number,
                "variants": [
                    {
                        "variant_id": var.variant_id,
                        "name": var.name,
                        "est_budget": var.est_budget,
                        "segments": [
                            serialize_segment(seg) for seg in var.segments
                        ],
                        "lodging_options": [
                            {
                                "name": lodge.name,
                                "type": lodge.type,
                                "avg_price_rub_per_night": get_price("lodging", lodge.name)
                            } for lodge in var.lodgings
                        ]
                    } for var in day.variants
                ]
            } for day in route.days
        ]
    })

def serialize_segment(seg):
    result = {
        "type": seg.type,
        "arrival_window": seg.arrival_window
    }

    if seg.type == "poi":
        result["poi"] = {
            "name": seg.poi_name,
            "must_see": seg.must_see,
            "rating": seg.rating
        }

    elif seg.type == "meal":
        result["meal"] = {
            "type": seg.meal_type,
            "options": json.loads(seg.meal_options_json or "[]")
        }

    elif seg.type == "transition":
        result["transition"] = {
            "walk_time_min": seg.walk_time_min,
            "walk_distance_m": seg.walk_distance_m,
            "reason": seg.transition_reason,
            "alt_options": json.loads(seg.alt_transport_json or "[]")
        }

    elif seg.type == "lodging":
        result["lodging"] = {
            "name": seg.lodging_name,
            "price": get_price("lodging", seg.lodging_name)
        }

    return result

@app.route('/api/session/<session_id>/vote', methods=['POST'])
def vote(session_id):
    data = request.json
    print(f"🗳 Голос за {session_id}: {data}")
    return jsonify({ "ok": True })

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'catalog_routes.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=PORT)
