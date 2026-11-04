from django.contrib.auth import views as auth
from django.urls import path
from . import views
urlpatterns = [
    path("login/", auth.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("logout/", auth.LogoutView.as_view(), name="logout"),
    path("keepalive/", views.keepalive, name="keepalive"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("my-bookings/", views.customer_home, name="customer_home"),
    path("staff/", views.staff_home, name="staff_home"),
    path("manager/", views.manager_home, name="manager_home"),
    path("manager/staff/new/", views.staff_new, name="staff_new"),
    path("manager/staff/<int:pk>/toggle/", views.staff_toggle, name="staff_toggle"),
]