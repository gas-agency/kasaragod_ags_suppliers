from django.urls import path
from . import views

urlpatterns = [
    path("apply/", views.apply, name="nc_apply"),
    path("mine/", views.my_applications, name="nc_list"),
    path("manage/", views.manage, name="nc_manage"),
    path("<str:application_no>/", views.detail, name="nc_detail"),
    path("<str:application_no>/file/<str:kind>/", views.document, name="nc_doc"),
]