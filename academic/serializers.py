"""Serializers usados por la API REST para validar datos JSON."""

from rest_framework import serializers

from .models import Order, Product


# Estos serializers trabajan con diccionarios provenientes del archivo JSON.
class ProductSerializer(serializers.Serializer):
    """Valida los productos disponibles en la tienda."""

    # El campo id se genera automáticamente al crear un nuevo registro.
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=150)
    description = serializers.CharField(max_length=500)
    price = serializers.IntegerField(min_value=0)
    stock = serializers.IntegerField(min_value=0)
    category = serializers.ChoiceField(choices=[choice[0] for choice in Product.CATEGORY_CHOICES])


class OrderSerializer(serializers.Serializer):
    """Valida una compra y sus líneas de carrito."""

    # La orden contiene información del cliente y el detalle de los productos comprados.
    id = serializers.IntegerField(read_only=True)
    customer_name = serializers.CharField(max_length=150)
    customer_email = serializers.EmailField()
    items = serializers.ListField(child=serializers.DictField(), allow_empty=False)
    total = serializers.IntegerField(min_value=0)
    status = serializers.ChoiceField(
        choices=[choice[0] for choice in Order.STATUS_CHOICES],
        read_only=True,
    )
