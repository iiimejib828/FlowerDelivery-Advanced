from django.conf import settings
from django.db import models
from django.contrib import admin
from django.utils.html import mark_safe
import os

def flower_image_upload_path(instance, filename):
    """Возвращает правильный путь для загрузки изображений"""
    return os.path.join("flowers", filename)

class Flower(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    image = models.ImageField(upload_to=flower_image_upload_path, verbose_name="Изображение")

    def __str__(self):
        return self.name

    def image_preview(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="50" height="50" />')
        return "Нет изображения"
    image_preview.short_description = "Превью изображения"

@admin.register(Flower)
class FlowerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "image_preview")
    search_fields = ("name",)
    readonly_fields = ("image_preview",)

