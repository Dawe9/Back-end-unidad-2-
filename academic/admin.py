"""Configuración del panel administrativo de Django."""

from django.contrib import admin

from .data_loader import load_store_data, save_store_data
from .models import Order, Product, Profile, Tenant


class TenantScopedAdmin(admin.ModelAdmin):
	"""Limita los registros del panel a la tienda del subadministrador."""

	def tenant_for_user(self, request):
		if request.user.is_superuser:
			return None
		return getattr(getattr(request.user, 'profile', None), 'tenant', None)

	def get_queryset(self, request):
		queryset = super().get_queryset(request)
		tenant = self.tenant_for_user(request)
		return queryset if tenant is None else queryset.filter(tenant=tenant)

	def save_model(self, request, obj, form, change):
		tenant = self.tenant_for_user(request)
		if tenant is not None:
			obj.tenant = tenant
		super().save_model(request, obj, form, change)

	def get_readonly_fields(self, request, obj=None):
		if request.user.is_superuser:
			return ()
		return ('tenant',)


@admin.register(Product)
class ProductAdmin(TenantScopedAdmin):
	list_display = ('name', 'tenant', 'price', 'stock', 'category')
	list_filter = ('tenant', 'category')

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		data = load_store_data()
		products = data['products']
		if obj.catalog_id is None:
			obj.catalog_id = max((item['id'] for item in products), default=0) + 1
			obj.save(update_fields=['catalog_id'])
		catalog_product = next((item for item in products if item['id'] == obj.catalog_id), None)
		payload = {
			'id': obj.catalog_id,
			'name': obj.name,
			'description': obj.description,
			'price': obj.price,
			'stock': obj.stock,
			'category': obj.category,
			'tenant': obj.tenant.name if obj.tenant else 'Cruzattour',
		}
		if catalog_product is None:
			products.append(payload)
		else:
			catalog_product.update(payload)
		save_store_data(data)


@admin.register(Order)
class OrderAdmin(TenantScopedAdmin):
	list_display = ('id', 'tenant', 'customer_name', 'total', 'status')
	list_filter = ('tenant', 'status')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'tenant')
	list_filter = ('tenant',)

	def get_queryset(self, request):
		queryset = super().get_queryset(request)
		if request.user.is_superuser:
			return queryset
		return queryset.filter(tenant=getattr(request.user.profile, 'tenant', None))

	def has_module_permission(self, request):
		return request.user.is_superuser


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug', 'created_at')
	readonly_fields = ('name', 'slug', 'created_at')
	fields = ('name', 'slug', 'display_name', 'primary_color', 'created_at')

	def has_module_permission(self, request):
		return request.user.is_superuser or hasattr(request.user, 'profile')

	def has_view_permission(self, request, obj=None):
		return request.user.is_superuser or hasattr(request.user, 'profile')

	def get_queryset(self, request):
		queryset = super().get_queryset(request)
		if request.user.is_superuser:
			return queryset
		return queryset.filter(pk=request.user.profile.tenant_id)

	def has_add_permission(self, request):
		return request.user.is_superuser

	def has_delete_permission(self, request, obj=None):
		return request.user.is_superuser
