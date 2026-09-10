"""Rutas globales del proyecto Django."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from academic import views

urlpatterns = [
    # Panel de administración opcional de Django.
    path('admin/', admin.site.urls),
    # Páginas visibles para el cliente de la tienda.
    path('', views.home, name='home'),
    path('products/', views.products_page, name='products'),
    path('cart/', views.cart_page, name='cart'),
    path('login/', views.login_page, name='login'),
    # Endpoints para autenticación JWT.
    path('api/token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('doc/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui-short'),
    # Todas las rutas REST comienzan con /api/.
    path('api/', include('academic.urls')),
]

# Django utiliza esta vista cuando ninguna URL coincide.
handler404 = 'academic.views.error_404'
