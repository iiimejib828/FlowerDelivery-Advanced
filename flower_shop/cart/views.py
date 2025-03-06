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
from django.utils import timezone
from .models import WorkingHours


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

def is_working_hours():
    """Проверяет, находится ли текущее время в рамках рабочего времени."""
    now = timezone.now()
    # Преобразуем в местное время согласно TIME_ZONE
    local_now = timezone.localtime(now)
    # Получаем текущий день недели (например, "mon")
    current_day = local_now.strftime("%a").lower()
    # Получаем текущее местное время
    current_time = local_now.time()
    try:
        working_hours = WorkingHours.objects.get(day=current_day)
        if working_hours.is_working and working_hours.opening_time <= current_time <= working_hours.closing_time:
            return True
    except WorkingHours.DoesNotExist:
        pass

    return False


@login_required
def checkout(request):
    """Оформление заказа"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    cart = request.session.get("cart", {})
    
    if request.method == "POST":
        # Проверка рабочего времени только при оформлении заказа
        if not is_working_hours():
            working_hours = WorkingHours.objects.filter(is_working=True)
            schedule = "\n".join(
                f"{wh.get_day_display()}: {wh.opening_time} - {wh.closing_time}"
                for wh in working_hours
            )
            return JsonResponse({
                "success": False,
                "message": f"К сожалению, мы можем принять заказ только в рабочее время.\nРасписание работы:\n\n{schedule}\n\nПожалуйста, попробуйте позже."
            })

        if not profile.phone:
            return JsonResponse({
                "success": False,
                "message": "Пожалуйста, заполните ваш профиль (номер телефона) перед оформлением заказа."
            })

        if not cart:
            return JsonResponse({
                "success": False,
                "message": "Ваша корзина пуста."
            })

        address = request.POST.get("address", "").strip()
        if not address:
            return JsonResponse({
                "success": False,
                "message": "Пожалуйста, укажите адрес доставки."
            })

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
        order.save()
        OrderItem.objects.bulk_create(items)

        request.session["cart"] = {}
        return JsonResponse({
            "success": True,
            "redirect_url": "/orders/"
        })

    # Обработка GET-запроса для отображения формы (всегда рендерим страницу)
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
