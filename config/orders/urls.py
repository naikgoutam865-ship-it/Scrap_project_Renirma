from django.urls import path
from . import views

urlpatterns = [
    path("buy/<int:artwork_id>/", views.buy_product, name="buy_product"),
    path("history/", views.order_history, name="order_history"),
    path("payment-success/", views.payment_success, name="payment_success")

]
