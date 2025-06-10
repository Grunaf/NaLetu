from collections import defaultdict, Counter
from datetime import date
import datetime
import time
import json, uuid

from flask import Flask, render_template, request, abort, jsonify, redirect, url_for, session
from models import db, Route, TripSession, Day, DayVariant, Segment, City, TripParticipant, TripVote
from services.get_api_transports import search_api_or_get_from_db_transports_from_city_to_city_on_date

def create_app(test_config=None):
    app = Flask(__name__)
    
    app.jinja_env.filters['loads'] = json.loads
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    if test_config is None:
        app.config.from_pyfile("config.py", silent=False)
    else:
        app.config.from_mapping(test_config)

    @app.context_processor
    def inject_common_vars():
        return {"cities": City.query.all()}
    
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
                "start_coords": [start.city.lat, start.city.lon],
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
                    "arrival": p.open_hours,
                    "rating": p.rating
                } for p in pois
            ]
            routes.append(data)

        return render_template('catalog.html', routes=routes)


    @app.route('/trip-setup')
    def trip_setup():
        session_id = request.args.get('sessionId')
        if not session_id:
            abort(400, 'sessionId обязателен')

        trip_session = db.session.get(TripSession, session_id)
        if not trip_session:
            abort(404, 'Сессия не найден')

        plan = {
            "session_id":                trip_session.id,
            "title":             trip_session.route.title,
            "durations_day":     trip_session.route.duration_days,
            "day_variants": [
                {
                    "day":      d.day_order,
                    "variants": [
                        {
                            "id": v.id,
                            "name":       v.name,
                            "est_budget": v.est_budget
                        } for v in d.variants
                    ]
                } for d in sorted(trip_session.route.days, key=lambda d: d.day_order)
            ]
        }

        participants = list(TripParticipant.query.filter_by(session_id=session_id))
        votes = [{
                    "participant_name": p.name,
                    "votes": {f"{v.day_order}": f"{v.day_variant.name}" for v in sorted(p.votes, key=lambda v:v.day_order) }
                } for p in participants if len(p.votes)]
        
        day_votes = {}
        for voter in votes:
            for day, variant_name in voter["votes"].items():
                day_votes.setdefault(day, []).append(variant_name)

        winner_variants = {
            day: Counter(variant_names).most_common(1)[0][0]
            for day, variant_names in day_votes.items()
        }

        expected_count_of_vote = len(TripParticipant.query.filter_by(session_id=session_id).all())
        is_completed_vote = expected_count_of_vote == len(votes)

        # freq_variants = defaultdict(int)
        # for p in participants:
        #     if len(p.votes):
        #         for d in range(trip_session.route.duration_days):
        #             freq_variants[f"{p.votes[d].variant_id}"] += 1
        # winner_variants = [max(participants, key=lambda p:p.votes[d]) for d in range(trip_session.route.duration_days) ]
        show_name_modal = False if session.get("participant_name") else True
        return render_template('trip-setup.html', show_name_modal=show_name_modal, is_completed_vote=is_completed_vote, votes=votes,
                               winner_variants=winner_variants, plan=plan, today=date.today())
    
    def format_transports(t):
        tickets = t.get("tickets_info")
        places = tickets.get("places") if tickets else []
        m = datetime.timedelta(seconds=int(t.get("duration")))
        formated_transports = {
                    "title":t.get("thread").get("title"),
                    "transport_type": t.get("thread").get("transport_type"),
                    "departure": t.get("departure"),
                    "arrival": t.get("arrival"),
                    "start_cost_rub": min(places, key=lambda p:p["price"]["whole"])["price"]["whole"] if len(places) else None,
                    "duration_min":  m
                }
        return formated_transports
    
    @app.before_request
    def ensure_participant_joined():
        session_id = request.args.get("sessionId")
        if session_id is None:
            return
        
        participant_name = session.get("participant_name")
        if participant_name is None:
            return
        
        existing_patricipant = TripParticipant.query.filter_by(name=participant_name).first()
        if existing_patricipant:
            return
        else:
            trip_participant = TripParticipant(name=participant_name, session_id=session_id)
            db.session.add(trip_participant)
            db.session.commit()

        

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

        votes = list(TripVote.query.filter_by(session_id=session_id).all())

        choices = [
            c[0] for c in Counter([v.day_variant for v in votes]).most_common(session.route.duration_days)
        ]
        days = []
        iter_list = iter([v for v in sorted(choices, key=lambda v: v.day.day_order)])
        for day in route.days:
            variant = next(iter_list, None)
            if variant:
                segments = sorted(variant.segments, key=lambda s: s.order)
                days.append({
                    "day_order": day.day_order,
                    "variant": variant,
                    "segments": segments,
                    "lodgings": variant.lodgings
                })

        transports_to_with_data_json = search_api_or_get_from_db_transports_from_city_to_city_on_date(session.start_date, session.city, route.cities[0].city)
        transports_from_with_data_json = search_api_or_get_from_db_transports_from_city_to_city_on_date(session.start_date, route.cities[0].city, session.city)
        transports_to_json = transports_to_with_data_json.data_json
        transports_from_json = transports_from_with_data_json.data_json
        transports = defaultdict()

        transports["there"] = [format_transports(t_to) for t_to in transports_to_json] 
        transports["back"] = [format_transports(t_from) for t_from in transports_from_json]

        return render_template("trip-itinerary.html", route=route, session=session, days=days, transports=transports)
    
    @app.route('/api/session/update_departure_city', methods=['POST'])
    def get_cities():
        data = request.json
        cities = City.query.all()
        if cities is None:
            return abort(404, "Городов нет в бд")
        return jsonify(cities)
    
    @app.route('/api/session/update_transports/', methods=['POST'])
    def update_transports_in_db():
        data = request.json or {}
        start_date = data.get('startDate')
        if start_date is None:
            abort(400, "Отсутствует дата для поиска")

        session_id = data.get('sessionId')
        if session_id is None:
            abort(400, "Отсутствует id session для поиска")
        session = db.session.get(TripSession, session_id)
        session.start_date = start_date
        db.session.commit()
        route = db.session.get(Route, session.route_id)

        _ = search_api_or_get_from_db_transports_from_city_to_city_on_date(session.start_date, session.city, route.cities[0].city)
        _ = search_api_or_get_from_db_transports_from_city_to_city_on_date(session.start_date, route.cities[0].city, session.city)
        return jsonify({"message": "Transport updated "})
    
    @app.route('/api/session', methods=['POST'])
    def create_session_or_get_exist():
        data = request.json or {}
        route_id   = data['routeId']
        departure_city_id   = data['departureCityId']
        # start_date   = data.get('checkIn')[:10]    # «YYYY-MM-DD»
        # end_date  = data.get('checkOut')[:10   ]
        if not (route_id): # and start_date and end_date
            abort(400, 'Нужно указать routeId') #, checkIn и checkOut
        exist_session = TripSession.query.filter_by(route_id=route_id).first() #,start_date=start_date,end_date=end_date
        if exist_session is not None: 
            return jsonify({"sessionId": exist_session.id})
        route = db.session.get(Route, route_id) #,start_date=start_date,end_date=end_date
        # try:
        #     ci = date.fromisoformat(start_date)
        #     co = date.fromisoformat(end_date)
        # except ValueError:
        #     abort(400, 'Неверный формат даты, ожидаются YYYY-MM-DD')
        sid = str(uuid.uuid4())
        session = TripSession(
            id=sid,
            route_id=route_id,
            departure_city_id=departure_city_id,
            start_date=datetime.datetime.today(),
            end_date=datetime.datetime.today() + datetime.timedelta(days=route.duration_days),
            choices_json='{}'
        )
        db.session.add(session)
        db.session.commit()
        return jsonify({"sessionId": session.id})
    
    @app.route("/api/session/save_participant_name", methods=["POST"])
    def save_participant_name():
        data = request.json or {}
        participant_name = data["participant_name"]
        session_id = data["session_id"]
        session["participant_name"] = participant_name
        trip_participant = TripParticipant(name=participant_name, session_id=session_id)
        db.session.add(trip_participant)
        db.session.commit()
        return jsonify({"message": "participant name added to db"})

    @app.route("/api/session/vote", methods=["POST"])
    def vote():
        data = request.json or {}
        choices = data["choices"]
        session_id = data["session_id"]
        participant_name = session.get("participant_name")
        if participant_name is None:
            abort(400, "пользователь не ввел имя")
        participant = TripParticipant.query.filter_by(name=participant_name).first()
        if participant is None:
            abort(400, "пользователь не найден")
        exist_participant_votes = TripVote.query.filter_by(participant_id=participant.id).all()
        trip_votes_to_add = []
        for choice in choices:
            if exist_participant_votes:
                for v_id, day_order in choice.items():
                    for vote in exist_participant_votes:
                        if vote.day_order == int(day_order) and vote.variant_id != int(v_id):
                            vote.variant_id = int(v_id)
            else:
                for v_id, day_order in choice.items():
                    trip_votes_to_add.append(TripVote(participant_id=participant.id, variant_id=v_id, day_order=day_order, session_id=session_id))
            
        db.session.add_all(trip_votes_to_add)
        db.session.commit()
        return jsonify({"message": "choices accepted"})

    return app