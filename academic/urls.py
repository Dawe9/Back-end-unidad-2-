"""URLs REST de la aplicación académico-comercial."""

from django.urls import path

from . import views

urlpatterns = [
    # Ruta raíz de la API: devuelve el recurso base de productos.
    path('', views.resource_list, {'resource': 'products'}, name='api-root'),
    # Esta ruta común sirve para listar y crear recursos.
    path('<str:resource>/', views.resource_list, name='resource-list'),
    # Detalle de un elemento concreto dentro de un recurso.
    path('<str:resource>/<int:record_id>/', views.resource_detail, name='resource-detail'),
]
