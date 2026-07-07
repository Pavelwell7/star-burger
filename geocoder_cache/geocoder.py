import requests
from django.conf import settings
from django.utils import timezone

from geocoder_cache.models import Place


def fetch_coordinates(address):
    try:
        response = requests.get(
            'https://geocode-maps.yandex.ru/1.x/',
            params={
                'geocode': address,
                'apikey': settings.YANDEX_GEOCODER_API_KEY,
                'format': 'json',
            },
            timeout=5,
        )
        response.raise_for_status()

        found_places = response.json()['response']['GeoObjectCollection']['featureMember']
        if not found_places:
            return None

        lon, lat = found_places[0]['GeoObject']['Point']['pos'].split(' ')
        return float(lat), float(lon)

    except (requests.exceptions.RequestException, KeyError, ValueError):
        return None


def get_coordinates_map(addresses):
    cached_places = Place.objects.filter(address__in=addresses)
    coordinates_map = {}
    cached_addresses = set()

    for place in cached_places:
        coordinates_map[place.address] = (place.lat, place.lon) if place.lat and place.lon else None
        cached_addresses.add(place.address)

    missing_addresses = set(addresses) - cached_addresses
    for address in missing_addresses:
        coords = fetch_coordinates(address)

        lat, lon = coords if coords else (None, None)
        place, created = Place.objects.get_or_create(
            address=address,
            defaults={
                'lat': lat,
                'lon': lon,
                'updated_at': timezone.now(),
            }
        )
        if not created and place.lat and place.lon:
            coordinates_map[address] = (place.lat, place.lon)
        else:
            coordinates_map[address] = coords

    return coordinates_map
