from django.contrib import admin
from django.utils.html import format_html
from .models import Slide

@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ("title", "preview", "button_text", "order", "active")
    list_editable = ("order", "active")
    ordering = ("order", "id")

    def preview(self, o):
        if o.image:
            return format_html('<img src="{}" style="height:48px;border-radius:6px">', o.image.url)
        return "No image"