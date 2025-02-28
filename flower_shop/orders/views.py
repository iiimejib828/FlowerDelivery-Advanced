from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order
from users.models import UserProfile


@login_required
def order_list(request):
    """Страница со списком заказов пользователя"""
    profile = get_object_or_404(UserProfile, user=request.user)
    orders = Order.objects.filter(user=profile).order_by("-created_at")
    
    return render(request, "orders/order_list.html", {"orders": orders})

@login_required
def repeat_order(request, order_id):
    """Повторение заказа (добавление товаров в корзину)"""
    profile = get_object_or_404(UserProfile, user=request.user)
    order = get_object_or_404(Order, id=order_id, user=profile)

    cart = request.session.get("cart", {})

    for item in order.items.all():
        cart[str(item.flower.id)] = cart.get(str(item.flower.id), 0) + item.quantity

    request.session["cart"] = cart
    messages.success(request, f"✅ Товары из заказа #{order.id} добавлены в корзину! Вы можете изменить их перед оформлением.")
    
    return redirect("view_cart")

@login_required
def cancel_order(request, order_id):
    """Отмена заказа через веб-интерфейс"""
    profile = get_object_or_404(UserProfile, user=request.user)
    order = get_object_or_404(Order, id=order_id, user=profile)

    # Проверяем, можно ли отменить заказ
    if order.status in ["awaiting_payment", "pending", "processing"]:
        order.status = "canceled"
        order.save()
        messages.success(request, f"✅ Заказ #{order.id} успешно отменен.")
    else:
        messages.error(request, f"❌ Нельзя отменить заказ #{order.id}: он уже отправлен или доставлен.")

    return redirect("order_list")