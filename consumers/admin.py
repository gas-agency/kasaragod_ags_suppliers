from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.urls import path
from .forms import ImportForm
from .importer import import_file
from .models import Consumer

@admin.register(Consumer)
class ConsumerAdmin(admin.ModelAdmin):
    list_display = ("consumer_no", "name", "phone", "category", "cylinder_type", "active", "user")
    list_filter = ("active", "category", "connection_type")
    search_fields = ("consumer_no", "name", "phone", "lpg_id")
    raw_id_fields = ("user",)
    change_list_template = "admin/consumers/consumer/change_list.html"

    def get_urls(self):
        extra = [path("import-excel/", self.admin_site.admin_view(self.import_excel), name="consumers_consumer_import")]
        return extra + super().get_urls()

    def import_excel(self, request):
        if not self.has_add_permission(request):
            raise PermissionDenied
        form = ImportForm(request.POST or None, request.FILES or None)
        result = None
        if request.method == "POST" and form.is_valid():
            f = form.cleaned_data["file"]
            try:
                result = import_file(f, f.name, dry=form.cleaned_data["preview"])
                if result["dry"]:
                    self.message_user(request, "Preview only. Nothing was saved.", messages.SUCCESS)
                else:
                    self.message_user(request, f"Import finished: {result['created']} added, {result['updated']} updated.", messages.SUCCESS)
            except ValueError as e:
                self.message_user(request, str(e), messages.ERROR)
            except Exception:
                self.message_user(request, "Could not read the file. Save it as .xlsx or .csv and try again.", messages.ERROR)
        ctx = dict(self.admin_site.each_context(request), title="Import consumers from Excel",
                   form=form, result=result, opts=self.model._meta, total=Consumer.objects.count())
        return render(request, "admin/consumers/consumer/import.html", ctx)