from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="admin_dashboard"),
    path("reports/<str:kind>/", views.report, name="report"),
    path("export/all/", views.export_all, name="export_all"),
    path("export/<str:kind>/", views.export, name="export"),
]