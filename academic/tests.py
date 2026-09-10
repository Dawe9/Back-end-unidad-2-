"""Pruebas de integración para la tienda y la API."""

from django.test import TestCase


class StorePagesAndApiTests(TestCase):
    # Comprueba que las páginas principales del sitio respondan correctamente.
    def test_store_pages_are_available(self):
        for path in ['/', '/products/', '/cart/', '/login/']:
            self.assertEqual(self.client.get(path).status_code, 200)

    # Verifica que la API expone el catálogo de productos con la estructura esperada.
    def test_api_returns_products(self):
        response = self.client.get('/api/products/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 8)
        self.assertIn('price', response.json()[0])

    # Confirma que un cliente autenticado puede crear una orden en la tienda.
    def test_customer_can_create_order(self):
        from django.contrib.auth import get_user_model

        get_user_model().objects.create_user(username='buyer', password='secret123')
        token_response = self.client.post('/api/token/', {
            'username': 'buyer',
            'password': 'secret123',
        }, content_type='application/json')
        self.client.defaults['HTTP_AUTHORIZATION'] = f"Bearer {token_response.json()['access']}"
        response = self.client.post('/api/orders/', {
            'customer_name': 'Ana Perez',
            'customer_email': 'ana@example.com',
            'items': [{'id': 1, 'quantity': 1}],
            'total': 39990,
        }, content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], 'recibida')

    # Valida que los filtros por categoría y precio se apliquen al catálogo.
    def test_product_filters_are_applied(self):
        response = self.client.get('/api/products/?category=Cordillera&min_price=30000')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 5)
