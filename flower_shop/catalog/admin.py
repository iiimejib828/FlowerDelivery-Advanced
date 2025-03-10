from django.contrib import admin
from .models import Flower

# Register your models here.
@admin.register(Flower)
class FlowerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "image_preview")
    search_fields = ("name",)
    readonly_fields = ("image_preview",)

