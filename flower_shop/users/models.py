import asyncio

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib import admin
from bot.utils import send_message

User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name="Пользователь",
                                related_name="profile")
    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True, verbose_name="Номер телефона")
    address = models.TextField(null=True, blank=True, verbose_name="Адрес доставки")
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True, verbose_name="Telegram ID")
    notified_to_join_bot = models.BooleanField(default=False, verbose_name="Уведомлен о боте")

    def __str__(self):
        return self.full_name

    @staticmethod
    def get_by_telegram_id(telegram_id):
        """Получает профиль пользователя по Telegram ID"""
        try:
            return UserProfile.objects.get(telegram_id=telegram_id)
        except UserProfile.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        if self.phone:
            cleaned_phone = str(self.phone).strip().replace(" ", "").replace("-", "")
            if cleaned_phone.startswith("8"):
                cleaned_phone = "+7" + cleaned_phone[1:]
            self.phone = cleaned_phone  # ✅ Сохраняем нормализованный номер
        super().save(*args, **kwargs)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создает профиль пользователя при его создании"""
    if created:
        UserProfile.objects.create(user=instance, full_name=instance.get_full_name())

@receiver(post_save, sender=UserProfile)
def notify_profile_update(sender, instance, **kwargs):
    """Отправка уведомления в Telegram при обновлении данных профиля и логирование."""
    if instance.telegram_id:
        message = (f"Ваш профиль был обновлен.\n"
                   f"ФИО: {instance.full_name}\n"
                   f"Телефон: {instance.phone}\n"
                   f"Адрес: {instance.address}")
        send_message(instance.telegram_id, message)
        NotificationLog.objects.create(user=instance, message=message)

class NotificationLog(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="Пользователь", null=True, blank=True, related_name="notifications")
    message = models.TextField(verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время")

    def __str__(self):
        return f"Уведомление - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "message")
    search_fields = ("user__full_name", "message")
    list_filter = ("created_at",)
