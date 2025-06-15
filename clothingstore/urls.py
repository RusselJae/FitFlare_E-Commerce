from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('products/', views.product_list, name='product_list'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('store-cart-selection/', views.store_cart_selection, name='store_cart_selection'),
    path('orders/history/', views.order_history, name='order_history'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('order/receipt/<int:order_id>/', views.order_receipt, name='order_receipt'),
    path('account/', views.account_settings, name='account_settings'),
    path('account/change-password/', views.change_password, name='change_password'),
    path('logout/', views.logout_view, name='logout'),
    path('contact/', views.contact, name='contact'),
    path('custom-admin/logout/', views.logout_view, name='admin_logout'),

    #admin urls
    path('custom-admin/', views.admin_dashboard, name='admin_dashboard'),
    path('custom-admin/products/', views.admin_products, name='admin_products'),
    path('custom-admin/products/create/', views.admin_product_create, name='admin_product_create'),
    path('custom-admin/products/<int:pk>/edit/', views.admin_product_edit, name='admin_product_edit'),
    path('custom-admin/products/<int:product_id>/delete/', views.admin_product_delete_view, name='admin_product_delete'),
    path('custom-admin/users/', views.admin_users, name='admin_users'),
    path('custom-admin/users/create/', views.admin_user_create, name='admin_user_create'),
    path('custom-admin/users/<int:pk>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('custom-admin/users/<int:pk>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('custom-admin/logout/', LogoutView.as_view(next_page='login'), name='admin_logout'),
    path('custom-admin/orders/', views.admin_orders, name='admin_orders'),
    path('custom-admin/orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('custom-admin/orders/<int:order_id>/delete/', views.admin_order_delete, name='admin_order_delete'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)