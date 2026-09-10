"""Configuración WSGI para el proyecto Django."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_project.settings')

# Punto de entrada para servidores compatibles con WSGI.
application = get_wsgi_application()
