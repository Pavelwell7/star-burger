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
