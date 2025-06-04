import os
import uuid
import requests
import json
from collections import Counter, defaultdict
from weasyprint import HTML

from flask import Flask, jsonify, make_response, redirect, request, send_from_directory, abort, render_template, session, url_for
from flask_migrate import Migrate
from models import TripParticipant, TripVote, db, TripSession, Route, City, RouteCity, Day, DayVariant, Segment, TransportCache, LodgingOption, PriceEntry
from datetime import datetime, timedelta
from sqlalchemy import and_


app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get("SECRET_KEY", "default-secret")
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://student:studentpass@localhost:5432/travel_diploma_project'
db.init_app(app)

YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
YANDEX_API_URL = os.getenv('YANDEX_API_URL')

# После app.config и db.init_app(app)
migrate = Migrate(app, db)

PORT = 3000
TRANSPORT_TYPE_TRANSLATIONS = {
    "bus": "Автобус",
    "suburban": "Пригородный поезд",
    "train": "Поезд",
    "express": "Экспресс"
}


# ====================
# UTILS
# ====================
def translate_transport_type(thread):
    # Если есть express_type — он важнее
    t = thread.get("express_type") or thread.get("transport_type")
    mapping = {
        "bus": "Автобус",
        "suburban": "Пригородный поезд",
        "train": "Поезд",
        "express": "Экспресс",
        "aeroexpress": "Аэроэкспресс"
    }
    return mapping.get(t.strip().lower(), t)

def get_transport_data(from_city: str, to_city: str, date: datetime):
    cache = TransportCache.query.filter_by(from_city=from_city, to_city=to_city, date_for=date).first()

    now = datetime.utcnow()
    expired = True

    if cache and cache.updated_at:
        cutoff = now - timedelta(minutes=60)
        expired = cache.updated_at < cutoff
    else:
        cache = None  # если нет даты обновления, считаем недействительным

    if cache and not expired:
        return cache  # ✅ Используем свежий кэш

    # 🔽 Обновляем (или создаём) кэш
    params = {
        'from': from_city,
        'to': to_city,
        'lang': 'ru_RU',
        'date': date.isoformat(),
        'apikey': YANDEX_API_KEY
    }

    resp = requests.get(YANDEX_API_URL, params=params)
    print(resp.url)
    if resp.status_code != 200:
        raise Exception(f"Ошибка API Яндекса: {resp.status_code}, {resp.text}")

    data = resp.json()
    segments = data.get('segments', [])
    if not segments:
        return []
    
    for seg in segments:
        thread = seg.get("thread", {})
        thread["translated_type"] = translate_transport_type(thread)


    # либо обновляем существующий, либо создаём новый
    if cache:
        cache.transport_data_json = json.dumps(segments)
        cache.updated_at = now
    else:
        cache = TransportCache(
            from_city=from_city,
            to_city=to_city,
            transport_data_json=json.dumps(segments),
            date_for=date,
            updated_at= now
        )
        db.session.add(cache)

    db.session.commit()
    return cache


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
@app.template_filter()
def loads(value):
    import json
    return json.loads(value or "[]")

# ====================
# ROUTES
# ====================

CACHE_TTL = timedelta(minutes=45)


@app.route('/routes')
def catalog_routes():
    q = request.args.get("q", "").strip().lower()
    theme = request.args.get("theme")

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
                "arrival": p.arrival_window,
                "description": p.poi_description_json
            } for p in pois
        ]

        
        # 🔍 фильтрация
        title_match = q in r.title.lower()
        poi_match = any(q in (p.poi_name or "").lower() for p in pois)
        theme_match = True  # (расширяется позже)

        if q and not (title_match or poi_match):
            continue
        if theme and theme != "Все темы":
            # нужно добавить связь темы с маршрутом, если она есть
            theme_match = False  # пока отключено

        if theme_match:
            routes.append(data)
    return render_template('catalog.html', routes=routes)

@app.route('/trip-setup')
def trip_setup():
    session_id = request.args.get('session_id')
    if not session_id:
        abort(400, 'sessionId обязателен')

    trip_session = TripSession.query.get(session_id)
    if not trip_session:
        abort(404, 'Сессия не найдена')

    route = Route.query.get(trip_session.route_id)
    if not route:
        abort(404, 'Маршрут не найден')

    participant_name = session.get("participant_name")
    show_modal = participant_name is None

    # Собираем план по маршруту
    itinerary = {
        "id":                route.id,
        "title":             route.title,
        "session_id":        session_id,
        "voted":             trip_session.choices_json,
        "day_variants": [
            {
                "day":      d.day_number,
                "variants": [
                    {
                        "variant_id": v.variant_id,
                        "name":       v.name,
                        "est_budget": v.est_budget,
                        "segments":   v.segments
                    } for v in d.variants
                ]
            }
            for d in sorted(route.days, key=lambda d: d.day_number)
        ]
    }

    # Все голоса по сессии
    votes_raw = TripVote.query.filter_by(session_id=session_id).all()

    # Преобразуем в формат [{"name": ..., "choices": {"1": "...", "2": "..."}}]
    votes_dict = defaultdict(lambda: {"name": "", "choices": {}})

    for vote in votes_raw:
        name = vote.participant.name
        votes_dict[name]["name"] = name
        votes_dict[name]["choices"][str(vote.day_number)] = vote.variant_id

    votes = list(votes_dict.values())


    # ✅ Подсчёт победителей по каждому дню
    day_votes = {}
    for voter in votes:
        for day, variant_id in voter["choices"].items():
            day_votes.setdefault(day, []).append(variant_id)

    winners = {
        day: Counter(variant_ids).most_common(1)[0][0]
        for day, variant_ids in day_votes.items()
    }

    expected_voter_count = TripParticipant.query.filter_by(session_id=session_id).count()
    voting_complete = len(votes) >= expected_voter_count

    return render_template('trip-setup.html', itinerary=itinerary, session_id=session_id, votes=votes, winners=winners, voting_complete=voting_complete, show_modal=show_modal)

@app.before_request
def ensure_participant_tracked():
    session_id = request.args.get("session_id")
    if not session_id:
        return

    # 1. Получаем имя участника из cookie-сессии браузера
    participant_name = session.get('participant_name')

    if participant_name:
        # 2. Проверяем: есть ли уже запись об этом участнике в этой сессии
        existing = TripParticipant.query.filter_by(session_id=session_id, name=participant_name).first()
        if not existing:
            # 🔁 создаём новую запись для НОВОЙ сессии, даже если имя уже есть
            new_participant = TripParticipant(session_id=session_id, name=participant_name)
            db.session.add(new_participant)
            db.session.commit()

@app.route("/api/save-name", methods=["POST"])
def save_participant_name():
    data = request.get_json()
    session_id = data.get("session_id")
    name = data.get("name")

    if not session_id or not name:
        return jsonify({"status": "error", "message": "Данные отсутствуют"}), 400

    existing = TripParticipant.query.filter_by(session_id=session_id, name=name).first()

    if not existing:
        participant = TripParticipant(session_id=session_id, name=name)
        db.session.add(participant)
        db.session.commit()
    else:
        participant = existing

    # Сохраняем в flask_session
    session["participant_name"] = name
    session["participant_id"] = participant.id
    session["session_id"] = session_id
    return jsonify({"status": "ok"})

@app.route('/trip-itinerary')
def trip_itinerary():
    session_id = request.args.get('session_id')
    if not session_id:
        abort(400)

    session = TripSession.query.get(session_id)
    if not session:
        abort(404)

    # Получение yandex_code города отправления
    if not session.city or not session.city.yandex_code:
        abort(400, "Город отправления не указан или не имеет yandex_code")
    from_code = session.city.yandex_code

    # Получение маршрута
    route = Route.query.get(session.route_id)
    if not route:
        abort(404)

    # Получение города назначения
    route_city = RouteCity.query.filter_by(route_id=route.id).order_by(RouteCity.order).first()
    if not route_city or not route_city.city or not route_city.city.yandex_code:
        abort(400, "Город назначения не указан или не имеет yandex_code")
    to_code = route_city.city.yandex_code
    
    start_date = session.check_in or datetime.utcnow().date()
    end_date = start_date + timedelta(days=route.duration_days - 1)

    if from_code == to_code:
        transports_to = []
        transports_from = []
    else:
        transports_to = get_transport_data(from_code, to_code, start_date)
        transports_from = get_transport_data(to_code, from_code, end_date)

    # 🔽 Получение голосов из TripVote
    votes = TripVote.query.filter_by(session_id=session.id).all()

    # Подсчёт победивших вариантов
    from collections import Counter, defaultdict
    day_votes = defaultdict(list)
    for vote in votes:
        day_votes[str(vote.day_number)].append(vote.variant_id)

    winners = {
        day: Counter(variant_ids).most_common(1)[0][0]
        for day, variant_ids in day_votes.items()
    }

    days = []
    for day in route.days:
        selected_variant_id = winners.get(str(day.day_number))
        variant = next((v for v in day.variants if v.variant_id == selected_variant_id), None)
        if variant:
            segments = sorted(variant.segments, key=lambda s: s.id)
            days.append({
                "day_number": day.day_number,
                "variant": variant,
                "segments": segments,
                "lodgings": variant.lodgings
            })

    return render_template(
        "trip-itinerary.html",
        itinerary=route,
        session=session,
        days=days,
        transports_from=transports_from,
        transports_to=transports_to,
    )


@app.route("/update-transport", methods=["POST"])
def update_transport_for_session():
    data = request.get_json()
    session_id = data.get("session_id")
    start_date_str = data.get("start_date")

    if not session_id or not start_date_str:
        return jsonify({"status": "error", "message": "Недостаточно данных"}), 400

    session_obj = TripSession.query.get(session_id)
    if not session_obj:
        return jsonify({"status": "error", "message": "Сессия не найдена"}), 404

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = start_date + timedelta(days=session_obj.route.duration_days - 1)

    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка в дате: {str(e)}"}), 400

    try:
        from_code = session_obj.city.yandex_code
        to_code = session_obj.route.cities[0].city.yandex_code

        # 🛫 Обновляем транспорт в оба направления
        _ = get_transport_data(from_code, to_code, start_date)
        _ = get_transport_data(to_code, from_code, end_date)

        session_obj.check_in = start_date
        db.session.commit()
    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка API: {str(e)}"}), 500

    return jsonify({"status": "ok"})

def inject_selected_meals_and_lodgings(days, selected_meal_names, selected_lodging_names):
    meal_set = set(selected_meal_names)
    lodging_set = set(selected_lodging_names)

    for day in days:
        # Для каждого meal-сегмента сохраняем только выбранный
        for seg in day["segments"]:
            if seg.type == "meal":
                options = json.loads(seg.meal_options_json)
                selected = next((opt for opt in options if opt.get("name", "").strip().lower() in meal_set), None)
                seg.selected_meal = selected

        # Для каждого дня — только один выбранный lodging
        selected_lodging = next((l for l in day["lodgings"] if l.name.strip().lower() in lodging_set), None)
        day["selected_lodging"] = selected_lodging


@app.route("/export-pdf", methods=["POST"])
def export_pdf_from_form():
    session_id = request.form.get("session_id")
    if not session_id:
        return "session_id обязателен", 400

    session_obj = TripSession.query.get(session_id)
    if not session_obj:
        return "Сессия не найдена", 404

    route = Route.query.get(session_obj.route_id)
    if not route:
        return "Маршрут не найден", 404

    # 🧭 Получаем даты
    start_date_str = request.form.get("start_date")
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = start_date + timedelta(days=route.duration_days - 1)
    except Exception:
        start_date = end_date = None

    # 📊 Победившие варианты
    votes = TripVote.query.filter_by(session_id=session_id).all()
    day_votes = defaultdict(list)
    for vote in votes:
        day_votes[str(vote.day_number)].append(vote.variant_id)
    winners = {
        day: Counter(variant_ids).most_common(1)[0][0]
        for day, variant_ids in day_votes.items()
    }

    # 📅 Дни маршрута
    days = []
    for day in route.days:
        selected_variant_id = winners.get(str(day.day_number))
        variant = next((v for v in day.variants if v.variant_id == selected_variant_id), None)
        if variant:
            segments = sorted(variant.segments, key=lambda s: s.id)
            days.append({
                "day_number": day.day_number,
                "variant": variant,
                "segments": segments,
                "lodgings": variant.lodgings
            })

    # 🧾 Выбранные значения
    try:
        selected_meals = json.loads(request.form.get("selected_meals") or "[]")
        selected_lodgings = json.loads(request.form.get("selected_lodgings") or "[]")
    except Exception:
        selected_meals = []
        selected_lodgings = []

    selected_lodging_names = [l.get("name", "").strip().lower() for l in selected_lodgings]
    selected_meal_names = [m.get("name", "").strip().lower() for m in selected_meals]
    inject_selected_meals_and_lodgings(days, selected_meal_names, selected_lodging_names)


    selected_transport_from = request.form.get("selected_transport_from", "")
    selected_transport_to = request.form.get("selected_transport_to", "")
    total_cost = request.form.get("totalCost", "?")

    html_out = render_template(
        "trip-itinerary-pdf.html",
        itinerary=route,
        session=session_obj,
        days=days,
        selected_transport_from=selected_transport_from,
        selected_transport_to=selected_transport_to,
        start_date=start_date,
        end_date=end_date,
        total_cost=total_cost,
        translate_transport_type=translate_transport_type
    )

    try:
        pdf = HTML(string=html_out).write_pdf()
    except Exception as e:
        return f"Ошибка при генерации PDF: {str(e)}", 500
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=trip.pdf'
    return response

@app.route('/start_trip_session')
def start_trip_session():
    route_id = request.args.get('route_id')
    if not route_id:
        abort(400, 'Нужно указать routeId')

    sid = str(uuid.uuid4())
    session = TripSession(
        id=sid,
        route_id=route_id,
        city_id=1,
        choices_json='{}'
    )
    db.session.add(session)
    db.session.commit()
    return redirect(url_for('trip_setup', session_id=sid))

@app.route('/api/transport-options')
def get_transport_options():
    from_city = request.args.get('from')
    to_city = request.args.get('to')
    if not from_city or not to_city:
        return jsonify({"error": "from и to обязательны"}), 400

    # Проверка кэша
    cached = TransportCache.query.filter_by(from_city=from_city, to_city=to_city).first()
    if cached and datetime.utcnow() - cached.updated_at < CACHE_TTL:
        return jsonify(cached.transport_data)

    # Заглушка запроса к API (реализуй реальный запрос)
    api_response = get_transport_data(from_city, to_city)
    if not api_response:
        return jsonify({"error": "не удалось получить данные от API"}), 500

    # Обновление кэша
    if cached:
        cached.transport_data = api_response
        cached.updated_at = datetime.utcnow()
    else:
        cached = TransportCache(
            from_city=from_city,
            to_city=to_city,
            transport_data=api_response
        )
        db.session.add(cached)
    db.session.commit()

    return jsonify(api_response)


@app.route('/api/plan/<route_id>')
def get_plan(route_id):
    route = Route.query.get(route_id)
    if not route:
        return abort(404)

    return jsonify({
        "id": route.id,
        "title": route.title,
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

# @app.route('/api/transport-to/<city>')
# def get_transport_to(city):
#     options = TransportOption.query.filter_by(destination_city=city).all()
#     result = []
#     for opt in options:
#         result.append({
#             "mode": opt.mode,
#             "description": opt.description,
#             "time_min": opt.time_min,
#             "cost_rub": opt.cost_rub
#         })
#     return jsonify(result)

@app.route("/api/session/<session_id>/vote", methods=["POST"])
def vote(session_id):
    trip_session = TripSession.query.get(session_id)
    if not trip_session:
        abort(404)

    # Получаем ID участника из сессии браузера
    participant_id = session.get("participant_id")
    if not participant_id:
        return {"status": "error", "message": "Участник не найден в сессии"}, 400

    participant = TripParticipant.query.get(participant_id)
    if not participant:
        return {"status": "error", "message": "Некорректный участник"}, 400

    # Удаляем предыдущие голоса этого участника по этой сессии
    TripVote.query.filter_by(participant_id=participant.id, session_id=session_id).delete()

    # Собираем новый выбор
    choices = {}
    for key, value in request.form.items():
        if key.startswith("day"):
            day = int(key.replace("day", ""))
            choices[day] = value

            vote = TripVote(
                session_id=session_id,
                participant_id=participant.id,
                day_number=day,
                variant_id=value
            )
            db.session.add(vote)

    db.session.commit()

    return {"status": "ok", "message": f"Голос учтён для {participant.name}. Обновите страницу, чтобы перейти дальше", "choices": choices}



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
