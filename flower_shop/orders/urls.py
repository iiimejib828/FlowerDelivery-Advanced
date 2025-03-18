from django.urls import path
from .views import order_list, repeat_order, cancel_order

urlpatterns = [
    path("orders/", order_list, name="order_list"),
    path("orders/repeat/<int:order_id>/", repeat_order, name="repeat_order"),
    path("orders/cancel/<int:order_id>/", cancel_order, name="cancel_order"),
]
