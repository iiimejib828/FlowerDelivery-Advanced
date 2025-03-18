from django.db import models
from django.contrib import admin
from .models import NotificationLog
from .models import UserProfile  # Импортируем модель UserProfile

# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    # Поля, которые будут отображаться в списке записей
    list_display = ('user', 'user_email', 'full_name', 'phone', 'address', 'telegram_id', 'notified_to_join_bot')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email пользователя'

    # Поля, по которым можно искать записи
    search_fields = ('user__username', 'full_name', 'phone', 'address', 'telegram_id')

    # Поля, по которым можно фильтровать записи
    list_filter = ('notified_to_join_bot',)

    # Поля, которые можно редактировать прямо из списка записей
    list_editable = ('phone', 'address', 'telegram_id', 'notified_to_join_bot')

    # Поля, которые будут отображаться в форме редактирования
    fieldsets = (
        (None, {
            'fields': ('user', 'full_name', 'phone', 'address', 'telegram_id', 'notified_to_join_bot')
        }),
    )

    # Автозаполнение поля user при выборе пользователя
    raw_id_fields = ('user',)

    # Переопределяем виджеты для полей phone и address
    formfield_overrides = {
        models.CharField: {'widget': admin.widgets.AdminTextInputWidget(attrs={'style': 'width: 100px;'})},
        models.TextField: {'widget': admin.widgets.AdminTextareaWidget(attrs={'style': 'width: 200px; height: 50px;'})},
    }

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "message")
    search_fields = ("user__full_name", "message")
    list_filter = ("created_at",)
