from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "Kasaragod AGS Suppliers Admin"
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("shop/", include("shop.urls")),
    path("connection/", include("connection.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("", include("gas.urls")),
        path("", include("notices.urls")),
            path("consumers/", include("consumers.urls")),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)