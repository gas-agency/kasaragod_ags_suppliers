from django.contrib import admin
from django.utils.html import format_html
from .models import Banner, Notification

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "preview", "link", "order", "active")
    list_editable = ("order", "active")

    def preview(self, o):
        return format_html('<img src="{}" style="height:44px;border-radius:6px">', o.image.url) if o.image else "-"

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "read", "created")
    list_filter = ("read",)
    search_fields = ("user__username", "title")