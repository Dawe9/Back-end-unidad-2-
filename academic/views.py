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
from .models import Product, Profile, Tenant
from .serializers import OrderSerializer, ProductSerializer


TENANT_BY_USERNAME = {
    'andy': ('Cruzattour', 'cruzattour'),
    'maxi': ('Maxi Tours', 'maxi-tours'),
}


def home(request):
    # Vista principal de la tienda: renderiza la página de inicio.
    return render(request, 'academic/home.html')


def products_page(request):
    # Muestra la vista del catálogo de productos.
    return render(request, 'academic/products.html')


def cart_page(request):
    # La página puede abrirse, pero las operaciones del carrito requieren autenticación.
    return render(request, 'academic/cart.html')


def login_page(request):
    # Vista para autenticación del usuario en la storefront.
    return render(request, 'academic/login.html')


def get_or_create_user_tenant(user):
    """Obtiene el perfil y asigna la tienda configurada para la cuenta."""

    profile, _ = Profile.objects.get_or_create(user=user)
    tenant_name, tenant_slug = TENANT_BY_USERNAME.get(
        user.username.lower(),
        (user.username, user.username.lower()),
    )
    if profile.tenant is None or (
        user.username.lower() in TENANT_BY_USERNAME
        and profile.tenant.slug != tenant_slug
    ):
        tenant, _ = Tenant.objects.get_or_create(
            name=tenant_name,
            slug=tenant_slug,
        )
        profile.tenant = tenant
        profile.save()
    return profile.tenant


def products_for_tenant(request, data):
    """Devuelve un catálogo independiente y lo inicializa para una nueva tienda."""

    tenant_name = get_or_create_user_tenant(request.user).name if request.user.is_authenticated else 'Cruzattour'
    products = data['products']
    for product in products:
        product.setdefault('tenant', 'Cruzattour')

    tenant_products = [product for product in products if product['tenant'] == tenant_name]
    if not tenant_products and tenant_name != 'Cruzattour':
        next_id = max((product['id'] for product in products), default=0) + 1
        tenant_products = []
        base_products = list(products)
        for product in base_products:
            copy = {**product, 'id': next_id, 'tenant': tenant_name}
            next_id += 1
            products.append(copy)
            tenant_products.append(copy)
        save_store_data(data)
    return tenant_products


def tenant_filter_for_orders(user, records):
    """Limita las órdenes visibles al tenant de la cuenta autenticada."""

    if not user.is_authenticated:
        return records
    profile, _ = Profile.objects.get_or_create(user=user)
    tenant = get_or_create_user_tenant(user)
    profile.tenant = tenant
    profile.save()
    return [item for item in records if item.get('tenant') == tenant.name]


@api_view(['GET', 'POST'])
def cart_api(request):
    """Lee o guarda el carrito persistente del perfil y su tenant."""

    if not request.user.is_authenticated:
        return Response({'detail': 'Debes iniciar sesión para gestionar tu carrito.'}, status=401)

    profile, _ = Profile.objects.get_or_create(user=request.user)
    if profile.tenant is None:
        get_or_create_user_tenant(request.user)
        profile.refresh_from_db()

    if request.method == 'GET':
        tenant = profile.tenant
        return Response({
            'cart': profile.cart,
            'tenant': tenant.name if tenant else None,
            'display_name': tenant.display_name if tenant and tenant.display_name else tenant.name if tenant else None,
            'primary_color': tenant.primary_color if tenant else '#2f6042',
            'can_edit_page': request.user.is_staff,
        })

    cart_items = request.data.get('cart', [])
    profile.cart = cart_items
    profile.save()
    tenant = profile.tenant
    return Response({
        'cart': profile.cart,
        'tenant': tenant.name if tenant else None,
        'display_name': tenant.display_name if tenant and tenant.display_name else tenant.name if tenant else None,
        'primary_color': tenant.primary_color if tenant else '#2f6042',
        'can_edit_page': request.user.is_staff,
    })


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

    records = products_for_tenant(request, data)
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


def decrease_product_stock(products, items):
    """Descuenta las cantidades compradas y devuelve un error si no hay stock."""

    quantities = {}
    for item in items:
        product_id = item.get('id')
        quantity = item.get('quantity')
        if isinstance(product_id, bool) or not isinstance(product_id, int):
            return 'Cada producto comprado debe incluir un id valido.'
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            return 'Cada producto comprado debe tener una cantidad entera positiva.'
        quantities[product_id] = quantities.get(product_id, 0) + quantity

    products_by_id = {product['id']: product for product in products}
    for product_id, quantity in quantities.items():
        product = products_by_id.get(product_id)
        if product is None:
            return f'El producto {product_id} no existe.'
        if product.get('stock', 0) < quantity:
            return f'No hay stock suficiente para {product["name"]}.'

    for product_id, quantity in quantities.items():
        products_by_id[product_id]['stock'] -= quantity
    return None


@extend_schema(
    request=ProductSerializer,
    responses={200: ProductSerializer(many=True), 201: ProductSerializer},
    description='Lista productos u órdenes, o crea un producto en el recurso correspondiente.',
)
@api_view(['GET', 'POST'])
def resource_list(request, resource):
    """Lista registros o crea uno nuevo, asignando las órdenes al tenant actual."""

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
        elif resource == 'orders' and request.user.is_authenticated:
            records = tenant_filter_for_orders(request.user, records)
        return Response(serialize_records(resource, records))

    if not request.user.is_authenticated:
        return Response({'detail': 'Se requiere un token JWT para modificar la tienda.'}, status=401)

    # DRF valida los datos antes de persistirlos en el archivo JSON.
    serializer = SERIALIZERS[resource](data=request.data)
    serializer.is_valid(raise_exception=True)
    record = dict(serializer.validated_data)
    record['id'] = max((item['id'] for item in data[key]), default=0) + 1
    if resource == 'orders':
        if request.user.is_authenticated:
            tenant = get_or_create_user_tenant(request.user)
            record['tenant'] = tenant.name
        else:
            record['tenant'] = record.get('tenant') or 'default'
        record['status'] = 'recibida'
        products = products_for_tenant(request, data)
        stock_error = decrease_product_stock(products, record['items'])
        if stock_error:
            return Response({'detail': stock_error}, status=400)
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
    if resource == 'orders' and request.user.is_authenticated:
        records = tenant_filter_for_orders(request.user, records)
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

    # Para PATCH se conservan los campos que el cliente no envió.
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
