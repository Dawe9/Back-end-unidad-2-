"""Pruebas de integración para la tienda, la API y el inventario."""

from unittest.mock import patch

from django.test import TestCase


class StorePagesAndApiTests(TestCase):
    # Comprueba que las páginas principales estén disponibles para el navegador.
    def test_store_pages_are_available(self):
        for path in ['/', '/products/', '/cart/', '/login/']:
            self.assertEqual(self.client.get(path).status_code, 200)

    # Verifica que el catálogo conserve la estructura esperada de la API.
    def test_api_returns_products(self):
        response = self.client.get('/api/products/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 8)
        self.assertIn('price', response.json()[0])

    def test_configured_users_receive_separate_store_catalogs(self):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        andy = user_model.objects.create_user(username='andy', password='secret123')
        maxi = user_model.objects.create_user(username='maxi', password='secret123')

        for username in ('andy', 'maxi'):
            token_response = self.client.post('/api/token/', {
                'username': username,
                'password': 'secret123',
            }, content_type='application/json')
            self.client.defaults['HTTP_AUTHORIZATION'] = f"Bearer {token_response.json()['access']}"
            response = self.client.get('/api/products/')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json())
            self.assertTrue(all(product['tenant'] for product in response.json()))

        andy.refresh_from_db()
        maxi.refresh_from_db()
        self.assertNotEqual(andy.profile.tenant_id, maxi.profile.tenant_id)

    # Confirma que una cuenta autenticada puede crear una orden.
    def test_customer_can_create_order(self):
        from django.contrib.auth import get_user_model

        get_user_model().objects.create_user(username='buyer', password='secret123')
        token_response = self.client.post('/api/token/', {
            'username': 'buyer',
            'password': 'secret123',
        }, content_type='application/json')
        self.client.defaults['HTTP_AUTHORIZATION'] = f"Bearer {token_response.json()['access']}"
        products_response = self.client.get('/api/products/')
        product_id = products_response.json()[0]['id']
        response = self.client.post('/api/orders/', {
            'customer_name': 'Ana Perez',
            'customer_email': 'ana@example.com',
            'items': [{'id': product_id, 'quantity': 1}],
            'total': 39990,
        }, content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], 'recibida')

    def test_customer_order_decreases_product_stock(self):
        from django.contrib.auth import get_user_model

        get_user_model().objects.create_user(username='stock_buyer', password='secret123')
        token_response = self.client.post('/api/token/', {
            'username': 'stock_buyer',
            'password': 'secret123',
        }, content_type='application/json')
        self.client.defaults['HTTP_AUTHORIZATION'] = f"Bearer {token_response.json()['access']}"
        store_data = {
            'products': [{
                'id': 1,
                'name': 'Tour de prueba',
                'description': 'Producto para validar inventario.',
                'price': 1000,
                'stock': 5,
                'category': 'Cordillera',
                'tenant': 'stock_buyer',
            }],
            'orders': [],
        }

        with patch('academic.views.load_store_data', return_value=store_data), patch('academic.views.save_store_data'):
            response = self.client.post('/api/orders/', {
                'customer_name': 'Cliente Stock',
                'customer_email': 'stock@example.com',
                'items': [{'id': 1, 'quantity': 2}],
                'total': 2000,
            }, content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(store_data['products'][0]['stock'], 3)

    # Valida los filtros de categoría y precio del catálogo.
    def test_product_filters_are_applied(self):
        response = self.client.get('/api/products/?category=Cordillera&min_price=30000')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 5)

    def test_orders_are_filtered_by_user_tenant(self):
        # Crea una orden y comprueba que el tenant de la cuenta pueda verla.
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user = user_model.objects.create_user(username='tenant_user', password='secret123')
        token_response = self.client.post('/api/token/', {
            'username': 'tenant_user',
            'password': 'secret123',
        }, content_type='application/json')
        self.client.defaults['HTTP_AUTHORIZATION'] = f"Bearer {token_response.json()['access']}"
        product_id = self.client.get('/api/products/').json()[0]['id']

        self.client.post('/api/orders/', {
            'customer_name': 'Cliente Tenant',
            'customer_email': 'tenant@example.com',
            'items': [{'id': product_id, 'quantity': 1}],
            'total': 30000,
        }, content_type='application/json')

        response = self.client.get('/api/orders/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.json(), list))
        self.assertGreater(len(response.json()), 0)
        self.assertIn('tenant', response.json()[0])
