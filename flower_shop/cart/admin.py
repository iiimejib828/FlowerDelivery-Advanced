from django.contrib import admin
from .models import WorkingHours
# Register your models here.

@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ("day", "opening_time", "closing_time", "is_working")
    list_editable = ("opening_time", "closing_time", "is_working")

    def get_queryset(self, request):
        """Возвращает queryset с сортировкой по day_order."""
        qs = super().get_queryset(request)
        return qs.order_by("day_order")  # Сортировка по полю day_order