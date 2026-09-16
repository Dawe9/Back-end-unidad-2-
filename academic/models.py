"""Modelos principales de la tienda académica.

Estos modelos representan el catálogo de productos y las compras realizadas
por los clientes. La lógica de negocio se apoya en estos modelos para validar
las categorías, precios y estados de cada pedido.
"""

from django.contrib.auth.models import User
from django.db import models


class Tenant(models.Model):
    """Espacio aislado para un cliente u organización dentro del SaaS."""

    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    display_name = models.CharField(max_length=150, blank=True)
    primary_color = models.CharField(max_length=7, default='#2f6042')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name or self.name


class Profile(models.Model):
    """Perfil que vincula una cuenta, su tenant y su carrito persistente."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tenant = models.ForeignKey('Tenant', on_delete=models.SET_NULL, null=True, blank=True, related_name='profiles')
    cart = models.JSONField(default=list)

    def __str__(self):
        return f'{self.user.username} ({self.tenant.name if self.tenant else "sin tenant"})'


class Product(models.Model):
    """Producto disponible para la compra dentro de un tenant."""

    # Categorías usadas en la tienda para agrupar los productos por experiencia.
    CATEGORY_CHOICES = [
        ('Cordillera', 'Cordillera'),
        ('Aventura', 'Aventura'),
        ('Costa', 'Costa'),
        ('Cultura', 'Cultura'),
    ]

    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    catalog_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
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
    """Compra confirmada que pertenece al tenant del usuario que la crea."""

    # Estados por los que puede pasar una orden desde su creación hasta la entrega.
    STATUS_CHOICES = [
        ('recibida', 'Recibida'),
        ('preparando', 'Preparando'),
        ('enviada', 'Enviada'),
        ('entregada', 'Entregada'),
        ('cancelada', 'Cancelada'),
    ]

    tenant = models.ForeignKey('Tenant', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    items = models.JSONField()
    total = models.PositiveIntegerField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='recibida')
