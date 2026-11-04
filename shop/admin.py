from django.contrib import admin
from .models import Product, Order, OrderItem, TrackingEvent

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "active")
    list_editable = ("price", "stock", "active")
    list_filter = ("category", "active")
    search_fields = ("name",)

class ItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "name", "price", "qty")

class EventInline(admin.TabularInline):
    model = TrackingEvent
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_no", "name", "phone", "total", "payment_method", "payment_status", "status", "created")
    list_filter = ("status", "payment_method", "payment_status")
    search_fields = ("order_no", "name", "phone")
    readonly_fields = ("order_no", "gateway_order_id", "gateway_payment_id")
    inlines = [ItemInline, EventInline]