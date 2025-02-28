import asyncio
from bot.config import TOKEN
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .models import UserProfile

bot = Bot(token=TOKEN)

class CustomLoginView(LoginView):
    template_name = "users/login.html"  # ✅ Указываем правильный путь к шаблону
    """Вход с сохранением сессии"""
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, form.get_user())  # ✅ Принудительно обновляем сессию

        # 1️⃣ Определяем, куда перенаправить пользователя
        next_url = self.request.GET.get("next") or "/"

        # 2️⃣ Восстанавливаем корзину после входа
        session_cart = self.request.session.get("cart", {})
        if session_cart:
            profile, created = UserProfile.objects.get_or_create(user=self.request.user)
            profile.cart = session_cart  # ❗️Проверьте, что в `UserProfile` есть поле `cart`
            profile.save()

        return redirect(next_url)  # ✅ Перенаправляем на checkout, если он был в `next`

def register(request):
    """Регистрация нового пользователя и переход к заполнению профиля"""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile, created = UserProfile.objects.get_or_create(user=user, defaults={"full_name": user.username})
            login(request, user)  # ✅ Автоматический вход
            return redirect("profile")  # ✅ Перенаправление на заполнение профиля
    else:
        form = UserCreationForm()

    return render(request, "users/register.html", {"form": form})

@login_required
def profile(request):
    """Страница редактирования профиля"""
    profile = request.user.profile

    if request.method == "POST":
        profile.full_name = request.POST.get("full_name")
        profile.phone = request.POST.get("phone")
        profile.address = request.POST.get("address")
        new_email = request.POST.get("email")

        # Проверяем, изменился ли email
        if new_email and new_email != request.user.email:
            request.user.email = new_email
            request.user.save()
            update_session_auth_hash(request, request.user)

        # Проверяем Telegram ID
        telegram_id = request.POST.get("telegram_id", "").strip()
        if telegram_id.lower() == "none":
            telegram_id = None
        if profile.telegram_id and not telegram_id:
            if profile.telegram_id:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(bot.send_message(profile.telegram_id, "⚠️ Ваш Telegram отвязан от аккаунта."))
                except TelegramBadRequest:
                    pass  # Игнорируем ошибку, если Telegram ID неверный
            profile.telegram_id = None
        elif telegram_id and telegram_id != profile.telegram_id:
            profile.telegram_id = telegram_id
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(bot.send_message(profile.telegram_id, "✅ Ваш Telegram успешно привязан!"))
            except TelegramBadRequest:
                messages.error(request, "❌ Ошибка: указанный Telegram ID не найден.")
                return redirect("profile")  # Остаемся на странице профиля

        profile.save()
        messages.success(request, "✅ Профиль обновлен!")
        return redirect("profile")  # Остаемся на странице профиля

    return render(request, "users/profile.html", {"profile": profile})
