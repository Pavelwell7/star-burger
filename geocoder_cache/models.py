from django.db import models
from django.utils import timezone


class Place(models.Model):
    address = models.CharField(
        'адрес',
        max_length=200,
        unique=True,
    )
    lat = models.FloatField(
        'широта',
        null=True,
        blank=True,
    )
    lon = models.FloatField(
        'долгота',
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(
        'дата запроса к геокодеру',
        default=timezone.now,
    )

    class Meta:
        verbose_name = 'место'
        verbose_name_plural = 'места'

    def __str__(self):
        return self.address

