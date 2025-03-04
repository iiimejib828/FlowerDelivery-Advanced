from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from catalog.models import Flower
from orders.models import Order, OrderItem
from users.models import UserProfile
from bot.utils import send_message
from bot.config import ADMIN_IDS
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def add_to_cart(request, flower_id):
    """Добавление цветка в корзину (работает для всех пользователей)"""
    if request.method == "POST":
        if "cart" not in request.session:
            request.session["cart"] = {}
            request.session.modified = True

        cart = request.session["cart"]
        cart[str(flower_id)] = cart.get(str(flower_id), 0) + 1
        request.session["cart"] = cart
        request.session.modified = True

        return JsonResponse({"success": True, "quantity": cart[str(flower_id)]})

    return JsonResponse({"success": False})

@csrf_exempt
def update_cart(request, flower_id, quantity):
    """Обновление количества цветов в корзине с пересчётом итоговой суммы"""
    if request.method == "POST":
        cart = request.session.get("cart", {})

        if quantity > 0:
            cart[str(flower_id)] = quantity
        else:
            cart.pop(str(flower_id), None)

        request.session["cart"] = cart
        request.session.modified = True

        total_price = sum(get_object_or_404(Flower, id=f_id).price * qty for f_id, qty in cart.items())
        flower = get_object_or_404(Flower, id=flower_id)
        subtotal = flower.price * quantity if quantity > 0 else 0

        return JsonResponse({
            "success": True, 
            "quantity": quantity,
            "subtotal": subtotal, 
            "total_price": total_price
        })

    return JsonResponse({"success": False})

@csrf_exempt
def view_cart(request):
    """Просмотр корзины"""
    if "cart" not in request.session:
        request.session["cart"] = {}
        request.session.modified = True

    cart = request.session.get("cart", {})
    flowers = []
    total_price = 0

    for flower_id, quantity in cart.items():
        flower = get_object_or_404(Flower, id=flower_id)
        flowers.append({"flower": flower, "quantity": quantity, "subtotal": flower.price * quantity})
        total_price += flower.price * quantity

    return render(request, "cart/cart.html", {"flowers": flowers, "total_price": total_price})

@csrf_exempt
def remove_from_cart(request, flower_id):
    """Удаление одного цветка из корзины"""
    if request.method == "POST":
        cart = request.session.get("cart", {})

        if str(flower_id) in cart:
            del cart[str(flower_id)]
            request.session["cart"] = cart
            request.session.modified = True

        total_price = sum(get_object_or_404(Flower, id=f_id).price * qty for f_id, qty in cart.items())

        return JsonResponse({"success": True, "total_price": total_price})

    return JsonResponse({"success": False})

@csrf_exempt
def clear_cart(request):
    """Очистка всей корзины"""
    if request.method == "POST":
        request.session["cart"] = {}
        request.session.modified = True
        return JsonResponse({"success": True})

    return JsonResponse({"success": False})

@login_required
def checkout(request):
    """Оформление заказа"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if not profile.phone:
        messages.warning(request, "Пожалуйста, заполните ваш профиль (номер телефона) перед оформлением заказа.")
        return redirect("profile")

    cart = request.session.get("cart", {})
    if not cart:
        messages.warning(request, "Ваша корзина пуста.")
        return redirect("flower_list")

    if request.method == "POST":
        address = request.POST.get("address", "").strip()
        if not address:
            messages.error(request, "Пожалуйста, укажите адрес доставки.")
            return redirect("checkout")

        # Создаем заказ и сразу заполняем его
        order = Order(user=profile, status="awaiting_payment", address=address)
        total_price = 0
        items = []
        for flower_id, quantity in cart.items():
            flower = get_object_or_404(Flower, id=flower_id)
            subtotal = flower.price * quantity
            total_price += subtotal
            items.append(OrderItem(
                order=order,
                flower=flower,
                quantity=quantity,
                price=flower.price,
                subtotal=subtotal
            ))
        
        order.total_price = total_price
        # Сохраняем заказ и элементы одним вызовом
        order.save()
        OrderItem.objects.bulk_create(items)

        # Очищаем корзину
        request.session["cart"] = {}
        messages.success(request, "Ваш заказ успешно оформлен!")

        # Уведомление будет отправлено через сигнал post_save
        return redirect("order_list")

    flowers = []
    total_price = 0
    for flower_id, quantity in cart.items():
        flower = get_object_or_404(Flower, id=flower_id)
        subtotal = flower.price * quantity
        total_price += subtotal
        flowers.append({
            "flower": flower,
            "quantity": quantity,
            "subtotal": subtotal,
        })

    return render(request, "cart/checkout.html", {
        "flowers": flowers,
        "total_price": total_price,
        "profile": profile,
    })