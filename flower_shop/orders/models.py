import asyncio
from bot.utils import send_message
from users.models import UserProfile, NotificationLog
from catalog.models import Flower
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.timezone import now, timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib import admin
from django.utils.html import mark_safe
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

User = get_user_model()

SHOP_NAME = "Цветочная Лавка"
SHOP_NAME_E = "Цветочной Лавке"

class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='items')
    flower = models.ForeignKey(Flower, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена за единицу на момент заказа
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)  # Общая стоимость (цена * количество)

    def __str__(self):
        return f"{self.flower.name} x {self.quantity}"

class Order(models.Model):
    STATUS_CHOICES = [
        ("awaiting_payment", "Ожидает оплаты"),
        ("pending", "Ожидает обработки"),
        ("processing", "В обработке"),
        ("shipped", "Отправлен"),
        ("delivered", "Доставлен"),
        ("canceled", "Отменен"),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="Пользователь", related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="awaiting_payment", verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Общая стоимость заказа
    address = models.CharField(max_length=255, blank=True, null=True)  # Адрес доставки

    def __str__(self):
        return f"Заказ {self.id} - {self.user.full_name}"

    def is_payment_overdue(self):
        if self.status == "awaiting_payment":
            return now() > self.created_at + timedelta(hours=24)
        return False

    def duplicate_order(self):
        """Создание нового заказа на основе текущего."""
        new_order = Order.objects.create(user=self.user, status="awaiting_payment", total_price=self.total_price, address=self.address)
        for item in self.items.all():
            OrderItem.objects.create(order=new_order, flower=item.flower, quantity=item.quantity, price=item.price, subtotal=item.subtotal)
        return new_order

    def get_order_summary(self):
        """Формирует текстовое описание заказа для Telegram."""
        items_list = "\n".join([f"{item.flower.name} x {item.quantity} - {item.subtotal} руб." for item in self.items.all()])
        return (
            f"Заказ #{self.id}\n"
            f"Состав:\n{items_list}\n"
            f"Общая стоимость: {self.total_price} руб.\n"
            f"Адрес доставки: {self.address or 'Не указан'}"
        )

    def send_telegram_notification(self):
        """Отправка уведомления в Telegram с кнопкой 'Отменить' только для создания заказа."""
        if not self.user.telegram_id:
            return
        
        message = self.get_order_summary()
        # Кнопка "Отменить" только для первого сообщения при создании
        if self.status in ["awaiting_payment", "pending", "processing"]:
            callback_data = f"cancel_order_{self.id}"
            button = InlineKeyboardButton(text="Отменить заказ", callback_data=callback_data)
            keyboard = [[button]]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        else:
            reply_markup = None

        send_message(self.user.telegram_id, message, reply_markup=reply_markup)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "created_at")
    list_filter = ("status", "created_at", "user")
    search_fields = ("user__full_name", "user__phone", "id")
    actions = ["mark_as_shipped", "mark_as_delivered", "mark_as_canceled"]

    def mark_as_shipped(self, request, queryset):
        for order in queryset:
            order.status = "shipped"
            order.save()
        self.message_user(request, "Выбранные заказы отмечены как отправленные.")

    mark_as_shipped.short_description = "Отметить как отправленный"

    def mark_as_delivered(self, request, queryset):
        for order in queryset:
            order.status = "delivered"
            order.save()
        self.message_user(request, "Выбранные заказы отмечены как доставленные.")

    mark_as_delivered.short_description = "Отметить как доставленный"

    def mark_as_canceled(self, request, queryset):
        for order in queryset:
            order.status = "canceled"
            order.save()
        self.message_user(request, "Выбранные заказы отменены.")

    mark_as_canceled.short_description = "Отменить заказ"

@receiver(post_save, sender=Order)
def send_status_update(sender, instance, created, **kwargs):
    """Отправка уведомления пользователю при создании или изменении статуса заказа."""

    if not instance.user.telegram_id:
        if not instance.user.notified_to_join_bot:
            message = f"Пожалуйста, свяжитесь с ботом по номеру {instance.user.phone} и отправьте команду /start."
            instance.user.notified_to_join_bot = True
            instance.user.save()
            NotificationLog.objects.create(user=instance.user, message=message)
        return

    # Уведомление при создании заказа (с кнопкой "Отменить")
    if created and instance.status == "awaiting_payment":
        instance.send_telegram_notification()
    # Уведомление при изменении статуса (без кнопок)
    elif not created:
        if instance.status == "delivered":
            message = (
                f"Ваш заказ #{instance.id} доставлен!\n"
                f"Спасибо, что выбрали нас! Ждём вас снова в нашей {SHOP_NAME_E} 🌸"
            )
        else:
            message = f"Статус вашего заказа #{instance.id} изменён на: {instance.get_status_display()}"
        send_message(instance.user.telegram_id, message)
        NotificationLog.objects.create(user=instance.user, message=message)