"""Vistas de la aplicación académica.

Aquí se definen tanto las páginas HTML del frontend como las rutas API que
permiten consultar y manipular el catálogo y las órdenes almacenadas en JSON.
"""

from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .data_loader import load_store_data, save_store_data
from .filters import ProductFilter
from .models import Product
from .serializers import OrderSerializer, ProductSerializer


def home(request):
    # Vista principal de la tienda: renderiza la página de inicio.
    return render(request, 'academic/home.html')


def products_page(request):
    # Muestra la vista del catálogo de productos.
    return render(request, 'academic/products.html')


def cart_page(request):
    # Página del carrito con la vista de compra en curso.
    return render(request, 'academic/cart.html')


def login_page(request):
    # Vista para autenticación del usuario en la storefront.
    return render(request, 'academic/login.html')


SERIALIZERS = {
    'products': ProductSerializer,
    'orders': OrderSerializer,
}


DATA_KEYS = {
    'products': 'products',
    'orders': 'orders',
}


def records_for_response(resource, data):
    # Devuelve la colección de datos correspondiente al recurso solicitado.
    return data[DATA_KEYS[resource]]


def filtered_product_records(request, data):
    """Valida filtros con django-filter y los aplica sobre el catálogo JSON."""

    # El filterset reutiliza la validación del modelo Product sin consultar la BD.
    filterset = ProductFilter(data=request.query_params, queryset=Product.objects.none())
    if not filterset.is_valid():
        return None, filterset.errors

    records = data['products']
    filters = filterset.form.cleaned_data
    if filters.get('category'):
        records = [item for item in records if item['category'] == filters['category']]
    if filters.get('name'):
        name = filters['name'].lower()
        records = [item for item in records if name in item['name'].lower()]
    if filters.get('min_price') is not None:
        records = [item for item in records if item['price'] >= filters['min_price']]
    if filters.get('max_price') is not None:
        records = [item for item in records if item['price'] <= filters['max_price']]
    return records, None


def serialize_records(resource, records):
    # Convierte una lista de diccionarios en la respuesta JSON de DRF.
    return SERIALIZERS[resource](records, many=True).data


@extend_schema(
    request=ProductSerializer,
    responses={200: ProductSerializer(many=True), 201: ProductSerializer},
    description='Lista productos u órdenes, o crea un producto en el recurso correspondiente.',
)
@api_view(['GET', 'POST'])
def resource_list(request, resource):
    """Lista registros o crea uno nuevo dentro del JSON."""

    if resource not in SERIALIZERS:
        return Response({'detail': 'Recurso no encontrado.'}, status=404)
    data = load_store_data()
    key = DATA_KEYS[resource]

    if request.method == 'GET':
        records = records_for_response(resource, data)
        if resource == 'products':
            records, errors = filtered_product_records(request, data)
            if errors:
                return Response(errors, status=400)
        return Response(serialize_records(resource, records))

    if not request.user.is_authenticated:
        return Response({'detail': 'Se requiere un token JWT para modificar la tienda.'}, status=401)

    # DRF valida los datos recibidos antes de guardarlos en el archivo JSON.
    serializer = SERIALIZERS[resource](data=request.data)
    serializer.is_valid(raise_exception=True)
    record = dict(serializer.validated_data)
    record['id'] = max((item['id'] for item in data[key]), default=0) + 1
    if resource == 'orders':
        record['status'] = 'recibida'
    data[key].append(record)
    save_store_data(data)
    return Response(serializer_class_data(resource, record), status=201)


@extend_schema(
    request=ProductSerializer,
    responses={200: ProductSerializer, 204: None},
    description='Consulta, actualiza o elimina un producto o una orden.',
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def resource_detail(request, resource, record_id, course_id=None):
    """Consulta, actualiza o elimina un registro del JSON."""

    if resource not in SERIALIZERS:
        return Response({'detail': 'Recurso no encontrado.'}, status=404)
    data = load_store_data()
    records = data[DATA_KEYS[resource]]
    record = next((item for item in records if item['id'] == record_id), None)
    if record is None:
        return Response({'detail': 'Registro no encontrado.'}, status=404)

    if request.method == 'GET':
        return Response(serializer_class_data(resource, record))
    if not request.user.is_authenticated:
        return Response({'detail': 'Se requiere un token JWT para modificar la tienda.'}, status=401)
    if request.method == 'DELETE':
        records.remove(record)
        save_store_data(data)
        return Response(status=204)

    # Para PATCH se conservan los campos no enviados por el cliente.
    payload = {**record, **request.data}
    serializer = SERIALIZERS[resource](data=payload)
    serializer.is_valid(raise_exception=True)
    record.update(serializer.validated_data)
    save_store_data(data)
    return Response(serializer_class_data(resource, record))


def serializer_class_data(resource, record):
    # Serializa un único registro para devolverlo al cliente en formato JSON.
    return SERIALIZERS[resource](record).data


def error_404(request, exception):
    # Se conserva el código HTTP 404, pero se muestra una página entendible.
    return render(request, '404.html', status=404)
