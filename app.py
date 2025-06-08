import uuid
from flask import Flask, jsonify, request, send_from_directory, abort, render_template
from flask_migrate import Migrate
from models import db, Route, TripSession, Day, DayVariant, Segment, LodgingOption, PriceEntry
from datetime import datetime
from flaskr import create_app
import json
import os

from routes.hotels import hotels_bp

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# app = Flask(__name__, static_folder='static')
# app.jinja_env.filters['loads'] = json.loads
# app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app = create_app()
db.init_app(app)
# app.register_blueprint(hotels_bp)

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

# @app.route('/routes')
# def catalog_routes():
#     routes = []
#     for r in Route.query.all():
#         # берём первый город как базу
#         start = r.cities[0]
#         data = {
#             "id": r.id,
#             "title": r.title,
#             "duration_days": r.duration_days,
#             "estimated_budget_rub": r.estimated_budget_rub,
#             "img": r.img,
#             "start_coords": [start.lat, start.lon],
#         }

#         pois = (
#             Segment.query
#             .join(DayVariant, Segment.variant_id==DayVariant.id)
#             .join(Day, DayVariant.day_id==Day.id)
#             .filter(Day.route_id==r.id, Segment.type=='poi')
#             .all()
#         )
#         # 3) кладём список упрощённых POI
#         data["pois"] = [
#             {
#                 "name": p.poi_name,
#                 "arrival": p.arrival_window,
#                 "rating": p.rating
#             } for p in pois
#         ]
#         routes.append(data)

#     return render_template('catalog.html', routes=routes)


# @app.route('/trip-setup')
# def trip_setup():
#     route_id = request.args.get('routeId')
#     if not route_id:
#         abort(400, 'routeId обязателен')

#     route = db.session.get(Route, route_id)
#     if not route:
#         abort(404, 'Маршрут не найден')

#     # Собираем план по маршруту
#     plan = {
#         "id":                route.id,
#         "title":             route.title,
#         "day_variants": [
#             {
#                 "day":      d.day_number,
#                 "variants": [
#                     {
#                         "variant_id": v.variant_id,
#                         "name":       v.name,
#                         "est_budget": v.est_budget
#                     } for v in d.variants
#                 ]
#             }
#             for d in sorted(route.days, key=lambda d: d.day_number)
#         ]
#     }

#     return render_template('trip-setup.html', plan=plan)

# @app.route('/trip-itinerary')
# def trip_itinerary():
#     session_id = request.args.get('sessionId')
#     if not session_id:
#         abort(400)

#     session = db.session.get(TripSession, session_id)
#     if not session:
#         abort(404)

#     route = db.session.get(Route, session.route_id)
#     if not route:
#         abort(404)

#     # по дефолту берём первый variant каждого дня
#     days = []
#     for day in route.days:
#         variant = day.variants[0] if day.variants else None
#         if variant:
#             segments = sorted(variant.segments, key=lambda s: s.order)
#             days.append({
#                 "day_number": day.day_number,
#                 "variant": variant,
#                 "segments": segments,
#                 "lodgings": variant.lodgings
#             })

#     transports = route.transports

#     return render_template("trip-itinerary.html", route=route, days=days, transports=transports)




# # @app.route("trip-itinerary", methods=["POST"])
# # def trip_itinerary():
# #     session_id = request.args.get("sessionId")
# #     session = db.session.get(TripSession, session_id)
# #     route = db.session.get(Route, session.route_id)
# #     if route is None:
# #         abort(404)
# #     transports = route.transports
# #     days = route.days
# #     return render_template("trip-itinerary", route=route, transports=transports, days=days)







# @app.route('/api/session', methods=['POST'])
# def create_session():
#     data = request.json or {}
#     route_id   = data['routeId']
#     check_in   = data.get('checkIn')    # «YYYY-MM-DD»
#     check_out  = data.get('checkOut')
#     if not (route_id and check_in and check_out):
#         abort(400, 'Нужно указать routeId, checkIn и checkOut')
#     try:
#         ci = datetime.fromisoformat(check_in).date()
#         co = datetime.fromisoformat(check_out).date()
#     except ValueError:
#         abort(400, 'Неверный формат даты, ожидаются YYYY-MM-DD')
#     sid = str(uuid.uuid4())
#     session = TripSession(
#         id=sid,
#         route_id=route_id,
#         departure_city=data.get("departure")['name'],
#         departure_lat=data.get("departure")['lat'],
#         departure_lon=data.get("departure")['lon'],
#         check_in=ci,
#         check_out=co,
#         choices_json='{}'
#     )
#     db.session.add(session)
#     db.session.commit()
#     return jsonify({'sessionId': sid})


# @app.route('/api/routes')
# def get_routes():
#     routes = Route.query.all()
#     for r in routes:
#         # берём первую точку маршрута (минимальный order)
#         city = next(iter(r.cities), None)
#         r.start_coords = [city.lat, city.lon] if city else None

#     return jsonify([
#         {
#             "id": r.id,
#             "title": r.title,
#             "days": r.duration_days,
#             "budget": r.estimated_budget_rub,
#             "description": r.title,
#             "img": r.img,
#             "start_coords": r.start_coords

#         } for r in routes
#     ])
# # app.py

# # @app.route('/api/plan/<route_id>')
# # def get_variants_plan(route_id):
# #     route = Route.query.get(route_id)
# #     if not route:
# #         abort(404, 'Маршрут не найден')
# #     # Собираем основные данные
# #     return jsonify({
# #         "id": route.id,
# #         "title": route.title,
# #         "day_variants": [
# #           {
# #             "day": d.day_number,
# #             "variants": [
# #               {
# #                 "variant_id": v.variant_id,
# #                 "name":       v.name,
# #                 "est_budget": v.est_budget,
# #               } for v in d.variants
# #             ]
# #           } for d in route.days
# #         ]
# #     })

# @app.route('/api/session/<session_id>/plan')
# def get_plan(session_id):
#     session = TripSession.query.get(session_id)
#     if not session:
#         abort(404, 'Session не найдена')
#     # перепользуем вашу логику построения плана из /api/plan/<route_id>
#     route = Route.query.get(session.route_id)
#     if not route:
#         abort(404, 'Route не найдена')
        
#     # Составляем список городов маршрута (шаблона)
#     cities = [
#         {"name": c.name, "lat": c.lat, "lon": c.lon, "order": c.order}
#         for c in sorted(route.cities, key=lambda c: c.order)
#     ]

#     # Для удобства фронта возвращаем coords первого города
#     first = cities[0] if cities else None

#     return jsonify({
#     "session_id": session.id,                  # фронт ждёт именно это
#         "departure": {                             # новая отправная точка
#             "name": session.departure_city,
#             "lat":  session.departure_lat,
#             "lon":  session.departure_lon
#         },
#         "checkIn":   session.check_in.isoformat(),
#         "checkOut":  session.check_out.isoformat(),

#         "id":        route.id,
#         "title":     route.title,
#         "duration_days":           route.duration_days,
#         "estimated_budget_rub":    route.estimated_budget_rub,

#         "start_coords": first and {"lat": first["lat"], "lon": first["lon"]},

#         "transport": {
#             "options": [
#                 {
#                     "mode": t.mode,
#                     "start_city": {
#                         "name": t.start_city.name,
#                         "lat":  t.start_city.lat,
#                         "lon":  t.start_city.lon
#                     },
#                     "end_city": {
#                         "name": t.end_city.name,
#                         "lat":  t.end_city.lat,
#                         "lon":  t.end_city.lon
#                     },
#                     "start_time_min": t.start_time_min,
#                     "start_cost_rub": t.start_cost_rub,
#                     "end_time_min":   t.end_time_min,
#                     "end_cost_rub":   t.end_cost_rub
#                 } for t in route.transports
#             ]
#         },

#         "day_variants": [
#             {
#                 "day": day.day_number,
#                 "variants": [
#                     {
#                         "variant_id": var.variant_id,
#                         "name":       var.name,
#                         "est_budget": var.est_budget,
#                         "segments":   [serialize_segment(s) for s in var.segments],
#                         "lodging_options": [
#                             {
#                                 "name":                  l.name,
#                                 "type":                  l.type,
#                                 "avg_price_rub_per_night": get_price("lodging", l.name)
#                             } for l in var.lodgings
#                         ]
#                     } for var in day.variants
#                 ]
#             } for day in route.days
#         ],

#         # если нужно, можете ещё вернуть cities для отрисовки карты:
#         "cities": cities
#     })


# def serialize_segment(seg):
#     result = {
#         "type": seg.type,
#         "arrival_window": seg.arrival_window
#     }

#     if seg.type == "poi":
#         result["poi"] = {
#             "name": seg.poi_name,
#             "must_see": seg.must_see,
#             "rating": seg.rating
#         }

#     elif seg.type == "meal":
#         result["meal"] = {
#             "type": seg.meal_type,
#             "options": json.loads(seg.meal_options_json or "[]")
#         }

#     elif seg.type == "transition":
#         result["transition"] = {
#             "walk_time_min": seg.walk_time_min,
#             "walk_distance_m": seg.walk_distance_m,
#             "reason": seg.transition_reason,
#             "alt_options": json.loads(seg.alt_transport_json or "[]")
#         }

#     elif seg.type == "lodging":
#         result["lodging"] = {
#             "name": seg.lodging_name,
#             "price": get_price("lodging", seg.lodging_name)
#         }

#     return result

# @app.route('/api/session/<session_id>/vote', methods=['POST'])
# def vote(session_id):
#     data = request.json
#     print(f"🗳 Голос за {session_id}: {data}")
#     return jsonify({ "ok": True })


# @app.route('/<path:filename>')
# def static_files(filename):
#     return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=PORT)
