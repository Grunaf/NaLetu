from flask import Blueprint, request, jsonify, abort
from services.hotellook import lookup_hotels, get_hotels_prices

hotels_bp = Blueprint('hotels', __name__)

@hotels_bp.route('/api/hotels/lookup')
def hotels_lookup():
    q = request.args.get('query')
    if not q:
        abort(400, 'Нужен параметр query')
    try:
        results = lookup_hotels(q)
    except Exception as e:
        abort(502, f'Ошибка Hotellook lookup: {e}')
    return jsonify(results)

@hotels_bp.route('/api/hotels/prices')
def hotels_prices():
    check_in  = request.args.get('checkIn')
    check_out = request.args.get('checkOut')
    if not (check_in and check_out):
        abort(400, 'Нужно указать checkIn и checkOut')
    # один из трёх
    loc = request.args.get('location')
    loc_id = request.args.get('locationId')
    h_id = request.args.get('hotelId')
    if not (loc or loc_id or h_id):
        abort(400, 'Нужно указать location|locationId|hotelId')

    try:
        data = get_hotels_prices(
            check_in=check_in,
            check_out=check_out,
            location=loc,
            location_id=loc_id,
            hotel_id=h_id
        )
    except Exception as e:
        abort(502, f'Ошибка Hotellook prices: {e}')
    return jsonify(data)
