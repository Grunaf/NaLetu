import os
import requests

TRAVEL_PAY_HOTEL_API_KEY = os.getenv('TRAVEL_PAY_HOTEL_API_KEY')
LOOKUP_URL = 'https://engine.hotellook.com/api/v2/lookup.json'
CACHE_URL  = 'https://engine.hotellook.com/api/v2/cache.json'

def lookup_hotels(query: str, limit: int = 10) -> dict:
    params = {
        'query': query,
        'lang': 'ru',
        'lookFor': 'both',
        'limit': limit,
        'token': TRAVEL_PAY_HOTEL_API_KEY
    }
    resp = requests.get(LOOKUP_URL, params=params)
    resp.raise_for_status()
    return resp.json().get('results', {})

def get_hotels_prices(check_in: str,
                      check_out: str,
                      location: str = None,
                      location_id: str = None,
                      hotel_id: str = None,
                      limit: int = 10) -> dict:
    params = {
        'checkIn':  check_in,
        'checkOut': check_out,
        'currency': 'rub',
        'limit':    limit,
        'token':    TRAVEL_PAY_HOTEL_API_KEY
    }
    if location:
        params['location'] = location
    if location_id:
        params['locationId'] = location_id
    if hotel_id:
        params['hotelId'] = hotel_id

    resp = requests.get(CACHE_URL, params=params)
    resp.raise_for_status()
    return resp.json()
