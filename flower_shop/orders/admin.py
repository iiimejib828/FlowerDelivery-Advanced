from django.contrib import admin
from .models import Order
# Register your models here.
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
