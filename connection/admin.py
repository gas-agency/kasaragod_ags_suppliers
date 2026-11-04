from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import NewConnection

@admin.register(NewConnection)
class NewConnectionAdmin(admin.ModelAdmin):
    list_display = ("application_no", "name", "phone", "cylinder", "status", "created")
    list_filter = ("status", "connection_type")
    search_fields = ("application_no", "name", "phone")
    exclude = ("photo", "aadhaar_front", "aadhaar_back")
    readonly_fields = ("application_no", "user", "documents")

    def documents(self, o):
        if not o.pk: return "-"
        links = []
        for kind, label in (("photo", "Photo"), ("front", "Aadhaar front"), ("back", "Aadhaar back")):
            links.append(format_html('<a href="{}" target="_blank">{}</a>', reverse("nc_doc", args=[o.application_no, kind]), label))
        return format_html(" | ".join(["{}"] * len(links)), *links)