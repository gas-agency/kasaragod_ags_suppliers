from django.contrib import admin
from .models import Cylinder, Booking, Enquiry

@admin.register(Cylinder)
class CylinderAdmin(admin.ModelAdmin):
    list_display = ("name", "weight", "price", "available")
    list_editable = ("price", "available")

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "cylinder", "quantity", "status", "created")
    list_editable = ("status",)
    list_filter = ("status", "created")
    search_fields = ("name", "phone", "consumer_no")

admin.site.register(Enquiry)