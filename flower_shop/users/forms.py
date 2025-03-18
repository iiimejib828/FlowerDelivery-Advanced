from django import forms
from .models import UserProfile
import re

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["phone", "address"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Введите номер телефона"}),
            "address": forms.Textarea(attrs={"class": "form-control", "placeholder": "Введите адрес доставки", "rows": 3}),
        }

    def clean_phone(self):
        """Валидация номера телефона."""
        phone = self.cleaned_data.get("phone")
        if phone:
            # Пример простой валидации: номер должен содержать только цифры и начинаться с +7
            if not re.match(r"^\+7\d{10}$", phone):
                raise forms.ValidationError("Номер телефона должен быть в формате +7XXXXXXXXXX.")
        return phone