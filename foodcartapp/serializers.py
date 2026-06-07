from rest_framework.serializers import Serializer, ListSerializer
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from .models import Product


class OrderItemSerializer(Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )
    quantity = serializers.IntegerField()


class OrderSerializer(Serializer):
    firstname = serializers.CharField()
    lastname = serializers.CharField()
    phonenumber = PhoneNumberField()
    address = serializers.CharField()
    products = OrderItemSerializer(
        many=True,
        allow_empty=False
    )
