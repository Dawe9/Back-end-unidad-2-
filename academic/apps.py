"""Configuración de la aplicación Django de la tienda."""

from django.apps import AppConfig


class AcademicConfig(AppConfig):
    # Django usa este nombre para registrar la aplicación academic.
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'academic'
