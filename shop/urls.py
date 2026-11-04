from django.urls import path
from . import views

urlpatterns = [
    path("", views.shop_home, name="shop_home"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/", views.cart_add, name="cart_add"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("cart/remove/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("pay/verify/", views.payment_verify, name="payment_verify"),
    path("orders/", views.orders, name="orders"),
    path("orders/<str:order_no>/", views.order_detail, name="order_detail"),
    path("orders/<str:order_no>/pay/", views.order_pay, name="order_pay"),
        path("orders/<str:order_no>/payment/", views.pay_page, name="pay_page"),
    path("manage/", views.manage_orders, name="manage_orders"),
]