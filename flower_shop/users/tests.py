from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .forms import UserProfileForm
from .models import UserProfile, NotificationLog


User = get_user_model()

class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com"
        )

    def test_user_profile_creation(self):
        """Тест автоматического создания профиля пользователя."""
        profile = UserProfile.objects.get(user=self.user)
        self.assertIsNotNone(profile)  # Профиль должен быть создан
        self.assertEqual(profile.user, self.user)  # Профиль должен быть связан с пользователем

class UserProfileFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com"
        )
        self.profile, created = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={
                "full_name": "Test User",
                "phone": "+79991234567",
                "address": "ул. Ленина, 10"
            }
        )

    def test_form_valid(self):
        """Тест валидности формы."""
        form_data = {
            "phone": "+79991234567",
            "address": "ул. Ленина, 10"
        }
        form = UserProfileForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        """Тест невалидности формы."""
        form_data = {
            "phone": "invalid_phone",  # Некорректный номер телефона
            "address": "ул. Ленина, 10"
        }
        form = UserProfileForm(data=form_data, instance=self.profile)
        self.assertFalse(form.is_valid())  # Теперь форма должна быть невалидной

class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse("register")

    def test_register_view_get(self):
        """Тест GET-запроса на страницу регистрации."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")

    def test_register_view_post(self):
        """Тест POST-запроса на регистрацию пользователя."""
        data = {
            "username": "testuser",
            "password1": "testpass123",
            "password2": "testpass123"
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 302)  # Перенаправление после успешной регистрации
        self.assertTrue(User.objects.filter(username="testuser").exists())

class ProfileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com"
        )
        # Используем get_or_create для создания профиля, если он не существует
        self.profile, created = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={
                'full_name': 'Test User',
                'phone': '+79991234567',
                'address': 'ул. Ленина, 10'
            }
        )
        self.client.login(username="testuser", password="testpass123")
        self.profile_url = reverse("profile")

    def test_profile_view_get(self):
        """Тест GET-запроса на страницу профиля."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")

    def test_profile_view_post(self):
        """Тест POST-запроса на обновление профиля."""
        self.client.login(username="testuser", password="testpass123")  # Аутентификация пользователя
        data = {
            "full_name": "Updated User",
            "phone": "+79998887766",
            "address": "ул. Пушкина, 15",
            "email": "updated@example.com"
        }
        response = self.client.post(self.profile_url, data)
        self.assertEqual(response.status_code, 302)  # Перенаправление после успешного обновления
        self.profile.refresh_from_db()
        self.user.refresh_from_db()  # Обновляем данные пользователя
        self.assertEqual(self.profile.full_name, "Updated User")
        self.assertEqual(self.profile.phone, "+79998887766")
        self.assertEqual(self.profile.address, "ул. Пушкина, 15")
        self.assertEqual(self.user.email, "updated@example.com")  # Теперь email должен обновиться

class UserProfileSignalTest(TestCase):
    def test_profile_creation_signal(self):
        """Тест автоматического создания профиля при создании пользователя."""
        # Создаем нового пользователя
        user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com"
        )
    
        # Проверяем, что профиль был создан
        profile = UserProfile.objects.get(user=user)
        self.assertIsNotNone(profile)  # Профиль должен существовать
    
        # Проверяем, что профиль связан с правильным пользователем
        self.assertEqual(profile.user, user)
    
        # Проверяем, что ключевые поля профиля инициализированы правильно
        self.assertIsNone(profile.phone)  # Поле phone должно быть None по умолчанию
        self.assertIsNone(profile.address)  # Поле address должно быть None по умолчанию
        self.assertIsNone(profile.telegram_id)  # Поле telegram_id должно быть None по умолчанию

class UserIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.profile_url = reverse("profile")

    def test_register_login_profile(self):
        """Тест регистрации, входа и редактирования профиля."""
        # Регистрация
        register_data = {
            "username": "testuser",
            "password1": "testpass123",
            "password2": "testpass123"
        }
        response = self.client.post(self.register_url, register_data)
        self.assertEqual(response.status_code, 302)  # Перенаправление после регистрации

        # Вход
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, 302)  # Перенаправление после входа

        # Редактирование профиля
        profile_data = {
            "full_name": "Test User",
            "phone": "+79991234567",
            "address": "ул. Ленина, 10",
            "email": "test@example.com"
        }
        response = self.client.post(self.profile_url, profile_data)
        self.assertEqual(response.status_code, 302)  # Перенаправление после обновления профиля

        # Проверка данных профиля
        user = User.objects.get(username="testuser")
        profile = user.profile
        self.assertEqual(profile.full_name, "Test User")
        self.assertEqual(profile.phone, "+79991234567")
        self.assertEqual(profile.address, "ул. Ленина, 10")
        self.assertEqual(user.email, "test@example.com")

