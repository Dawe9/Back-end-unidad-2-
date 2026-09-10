"""Modelos principales de la tienda académica.

Estos modelos representan el catálogo de productos y las compras realizadas
por los clientes. La lógica de negocio se apoya en estos modelos para validar
las categorías, precios y estados de cada pedido.
"""

from django.db import models


class Product(models.Model):
    """Producto disponible para la compra."""

    # Categorías usadas en la tienda para agrupar los productos por experiencia.
    CATEGORY_CHOICES = [
        ('Cordillera', 'Cordillera'),
        ('Aventura', 'Aventura'),
        ('Costa', 'Costa'),
        ('Cultura', 'Cultura'),
    ]

    # Datos básicos del producto: nombre, descripción, precio, stock y tipo.
    name = models.CharField(max_length=150)
    description = models.TextField()
    price = models.PositiveIntegerField()
    stock = models.PositiveIntegerField()
    category = models.CharField(max_length=80, choices=CATEGORY_CHOICES)

    def __str__(self):
        # Muestra el nombre del producto en el administrador y otros formularios.
        return self.name


class Order(models.Model):
    """Compra confirmada por un cliente."""

    # Estados por los que puede pasar una orden desde su creación hasta la entrega.
    STATUS_CHOICES = [
        ('recibida', 'Recibida'),
        ('preparando', 'Preparando'),
        ('enviada', 'Enviada'),
        ('entregada', 'Entregada'),
        ('cancelada', 'Cancelada'),
    ]

    # Información de contacto y detalle de la compra en formato JSON.
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    items = models.JSONField()
    total = models.PositiveIntegerField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='recibida')
