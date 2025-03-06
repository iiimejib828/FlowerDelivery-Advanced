from django.db import models

class WorkingHours(models.Model):
    DAY_CHOICES = [
        ("mon", "Понедельник"),
        ("tue", "Вторник"),
        ("wed", "Среда"),
        ("thu", "Четверг"),
        ("fri", "Пятница"),
        ("sat", "Суббота"),
        ("sun", "Воскресенье"),
    ]
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    day_order = models.IntegerField(default=0, editable=False)  # Поле для порядка
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_working = models.BooleanField(default=True)

    def __str__(self):
        return self.get_day_display()

    def save(self, *args, **kwargs):
        """Устанавливаем порядок при сохранении."""
        day_order_map = {
            "mon": 0,
            "tue": 1,
            "wed": 2,
            "thu": 3,
            "fri": 4,
            "sat": 5,
            "sun": 6,
        }
        self.day_order = day_order_map.get(self.day, 0)
        super().save(*args, **kwargs)