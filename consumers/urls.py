from django.urls import path
from . import views

urlpatterns = [
    path("import/template/", views.template_download, name="consumer_template"),
]