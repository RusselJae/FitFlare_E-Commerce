from django.contrib import admin
from .models import Product, CartItem, Order, OrderItem

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'clothing_type', 'price', 'stock', 'created_at')
    list_filter = ('category', 'clothing_type')
    search_fields = ('name', 'description')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'date_added')
    list_filter = ('date_added',)
    search_fields = ('user__username', 'product__name')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'total_amount', 'status', 'created_at', 'payment_status')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('user__username', 'first_name', 'last_name', 'payment_id')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    list_filter = ('order',)
    search_fields = ('order__id', 'product__name')
