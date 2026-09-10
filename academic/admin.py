"""Configuración del panel administrativo de Django."""

from django.contrib import admin

from .models import Order, Product


# Registra los modelos para gestionarlos desde la interfaz de administración.
admin.site.register([Product, Order])
