import requests
from django.conf import settings


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

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(' ')
        return float(lat), float(lon)

    except requests.exceptions.RequestException:
        return None
