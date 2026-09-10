"""Configuración ASGI para el proyecto Django."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_project.settings')

# Punto de entrada para servidores compatibles con ASGI.
application = get_asgi_application()
