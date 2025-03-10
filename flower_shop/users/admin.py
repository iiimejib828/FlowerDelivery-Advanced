from django.contrib import admin
from .models import NotificationLog
# Register your models here.
@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "message")
    search_fields = ("user__full_name", "message")
    list_filter = ("created_at",)
