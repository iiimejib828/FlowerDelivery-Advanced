from django.urls import path
from .views import view_cart, add_to_cart, update_cart, clear_cart, checkout


urlpatterns = [
    path("", view_cart, name="view_cart"),
    path("add/<int:flower_id>/", add_to_cart, name="add_to_cart"),
    path("update/<int:flower_id>/<int:quantity>/", update_cart, name="update_cart"),
    path("clear/", clear_cart, name="clear_cart"), 
    path("checkout/", checkout, name="checkout"),
]
