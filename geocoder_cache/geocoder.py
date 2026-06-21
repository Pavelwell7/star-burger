import requests
from django.conf import settings
from django.utils import timezone

from geocoder_cache.models import Place


def fetch_coordinates(address):

    try:
        place = Place.objects.get(address=address)
        if place.lat is None or place.lon is None:
            return None
        return place.lat, place.lon
    except Place.DoesNotExist:
        pass

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
            Place.objects.create(address=address, lat=None, lon=None)
            return None

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(' ')
        lat, lon = float(lat), float(lon)

        Place.objects.create(
            address=address,
            lat=lat,
            lon=lon,
            updated_at=timezone.now(),
        )

        return lat, lon

    except requests.exceptions.RequestException:
        return None

def get_coordinates_map(addresses):

    cached_places = Place.objects.filter(address__in=addresses)
    coordinates_map = {}
    cached_addresses = set()
    for place in cached_places:
        if place.lat is not None and place.lon is not None:
            coordinates_map[place.address] = (place.lat, place.lon)
        else:
            coordinates_map[place.address] = None
        cached_addresses.add(place.address)

    missing_addresses = set(addresses) - cached_addresses
    for address in missing_addresses:
        coords = fetch_coordinates(address)
        coordinates_map[address] = coords

        Place.objects.create(
            address=address,
            lat=coords[0] if coords else None,
            lon=coords[1] if coords else None,
            updated_at=timezone.now(),
        )

    return coordinates_map
