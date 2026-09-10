"""Filtros reutilizables para buscar productos en la tienda."""

import django_filters

from .models import Product


class ProductFilter(django_filters.FilterSet):
    """Valida los filtros disponibles para el catálogo JSON."""

    # Permite filtrar por categoría siguiendo los valores del modelo Product.
    category = django_filters.ChoiceFilter(
        choices=Product.CATEGORY_CHOICES,
    )

    # Filtros de rango para el precio mínimo y máximo del producto.
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')

    # Búsqueda parcial y no sensible a mayúsculas/minúsculas por nombre.
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Product
        fields = ['category', 'min_price', 'max_price', 'name']