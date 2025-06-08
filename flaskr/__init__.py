from datetime import date
from flask import Flask, render_template, request, abort, jsonify
from models import Route, TripSession, Day, DayVariant, Segment, db
import json, uuid
from markupsafe import escape
from services import get_api_transports
def create_app(test_config=None):
    app = Flask(__name__)
    
    app.jinja_env.filters['loads'] = json.loads
    if test_config is None:
        app.config.from_pyfile("config.py", silent=False)
    else:
        app.config.from_mapping(test_config)

        
    @app.route('/routes')
    def catalog_routes():
        routes = []
        for r in Route.query.all():
            # берём первый город как базу
            start = r.cities[0]
            data = {
                "id": r.id,
                "title": r.title,
                "duration_days": r.duration_days,
                "estimated_budget_rub": r.estimated_budget_rub,
                "img": r.img,
                "start_coords": [start.lat, start.lon],
            }

            pois = (
                Segment.query
                .join(DayVariant, Segment.variant_id==DayVariant.id)
                .join(Day, DayVariant.day_id==Day.id)
                .filter(Day.route_id==r.id, Segment.type=='poi')
                .all()
            )
            # 3) кладём список упрощённых POI
            data["pois"] = [
                {
                    "name": p.poi_name,
                    "arrival": p.arrival_window,
                    "rating": p.rating
                } for p in pois
            ]
            routes.append(data)

        return render_template('catalog.html', routes=routes)


    @app.route('/trip-setup')
    def trip_setup():
        route_id = request.args.get('routeId')
        if not route_id:
            abort(400, 'routeId обязателен')

        route = db.session.get(Route, route_id)
        if not route:
            abort(404, 'Маршрут не найден')

        # Собираем план по маршруту
        plan = {
            "id":                route.id,
            "title":             route.title,
            "durations_day":     route.duration_days,
            "day_variants": [
                {
                    "day":      d.day_number,
                    "variants": [
                        {
                            "variant_id": v.variant_id,
                            "name":       v.name,
                            "est_budget": v.est_budget
                        } for v in d.variants
                    ]
                }
                for d in sorted(route.days, key=lambda d: d.day_number)
            ]
        }

        return render_template('trip-setup.html', plan=plan, today=date.today())

    @app.route('/trip-itinerary')
    def trip_itinerary():
        session_id = request.args.get('sessionId')
        if not session_id:
            abort(400)

        session = db.session.get(TripSession, session_id)
        if not session:
            abort(404)

        route = db.session.get(Route, session.route_id)
        if not route:
            abort(404)
        choices = json.loads(session.choices_json)
        # по дефолту берём первый variant каждого дня
        days = []
        for day in route.days:
            variant = next((v for v in day.variants if v.variant_id in choices), None)
            if variant:
                segments = sorted(variant.segments, key=lambda s: s.order)
                days.append({
                    "day_number": day.day_number,
                    "variant": variant,
                    "segments": segments,
                    "lodgings": variant.lodgings
                })

        transports = route.transports

        return render_template("trip-itinerary.html", route=route, days=days, transports=transports)
    

    @app.route('/api/session', methods=['POST'])
    def create_session_or_get_exist():
        data = request.json or {}
        route_id   = data['routeId']
        check_in   = data.get('checkIn')[:10]    # «YYYY-MM-DD»
        check_out  = data.get('checkOut')[:10   ]
        if not (route_id and check_in and check_out):
            abort(400, 'Нужно указать routeId, checkIn и checkOut')
        exist_session = TripSession.query.filter_by(route_id=route_id,check_in=check_in,check_out=check_out).first()
        if exist_session is not None: 
            return jsonify({"sessionId": exist_session.id})
        try:
            ci = date.fromisoformat(check_in)
            co = date.fromisoformat(check_out)
        except ValueError:
            abort(400, 'Неверный формат даты, ожидаются YYYY-MM-DD')
        sid = str(uuid.uuid4())
        session = TripSession(
            id=sid,
            route_id=route_id,
            departure_city=data.get("departure")['name'],
            departure_lat=data.get("departure")['lat'],
            departure_lon=data.get("departure")['lon'],
            check_in=ci,
            check_out=co,
            choices_json='{}'
        )
        db.session.add(session)
        db.session.commit()
        return jsonify({'sessionId': sid})
    
    @app.route("/api/session/<sessionId>/vote", methods=["POST"])
    def vote(sessionId):
        data = request.json or {}
        choices = data["choices"]
        session_id = sessionId
        if session_id is None:
            abort(400)
        session = db.session.get(TripSession, session_id)
        if session is None:
            abort(404)
        session.choices_json = json.dumps(choices)
        db.session.commit()
        return jsonify({"message": "choices accepted"})

    return app