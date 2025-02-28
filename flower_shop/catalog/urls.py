from django.urls import path
from .views import flower_list
from cart.views import add_to_cart, view_cart, remove_from_cart, update_cart

urlpatterns = [
    path("catalog/", flower_list, name="flower_list"),
    path("cart/", view_cart, name="view_cart"),
    path("cart/add/<int:flower_id>/", add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:flower_id>/", remove_from_cart, name="remove_from_cart"),
]
