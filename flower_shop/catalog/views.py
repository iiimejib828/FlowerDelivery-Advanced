from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from catalog.models import Flower
from orders.models import Order
from users.models import UserProfile
from bot.utils import send_message
from bot.config import ADMIN_IDS
from cart.views import add_to_cart, view_cart, remove_from_cart, update_cart

def flower_list(request):
    """Отображение каталога цветов"""
    flowers = Flower.objects.all()
    return render(request, "catalog/catalog.html", {"flowers": flowers})