from django import forms
from .models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["phone", "address"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Введите номер телефона"}),
            "address": forms.Textarea(attrs={"class": "form-control", "placeholder": "Введите адрес доставки", "rows": 3}),
        }
