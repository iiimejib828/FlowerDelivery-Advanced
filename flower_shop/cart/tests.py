from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import time  # Импортируем time из модуля datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models import Flower
from orders.models import Order, OrderItem
from users.models import UserProfile
from .models import WorkingHours
import json

class WorkingHoursModelTest(TestCase):
    def setUp(self):
        # Создаем объект WorkingHours для тестирования
        self.working_hours = WorkingHours.objects.create(
            day="mon",
            opening_time=time(9, 0, 0),  # Используем time для создания объекта времени
            closing_time=time(18, 0, 0),  # Используем time для создания объекта времени
            is_working=True
        )

    def test_working_hours_creation(self):
        """Тест создания объекта WorkingHours."""
        self.assertEqual(self.working_hours.day, "mon")
        self.assertEqual(self.working_hours.opening_time.strftime("%H:%M:%S"), "09:00:00")
        self.assertEqual(self.working_hours.closing_time.strftime("%H:%M:%S"), "18:00:00")
        self.assertTrue(self.working_hours.is_working)

    def test_working_hours_save_method(self):
        """Тест метода save для установки порядка дней недели."""
        self.assertEqual(self.working_hours.day_order, 0)  # Понедельник должен иметь порядок 0

class CartViewsTest(TestCase):
    def setUp(self):
        # Создаем клиент для тестирования
        self.client = Client()

        # Создаем тестового пользователя
        self.user = User.objects.create_user(username="testuser", password="testpass123", email="test@example.com")
        
        # Создаем или обновляем профиль пользователя
        self.profile, created = UserProfile.objects.get_or_create(user=self.user)
        self.profile.phone = "+79991234567"  # Явно задаём телефон
        self.profile.address = "ул. Ленина, 10"
        self.profile.save()  # Сохраняем изменения

        # Создаем тестовый цветок с изображением
        image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        self.flower = Flower.objects.create(name="Роза", price=500.00, image=image)

        # Авторизуем пользователя
        self.client.login(username="testuser", password="testpass123")

    def test_add_to_cart(self):
        """Тест добавления товара в корзину."""
        url = reverse("add_to_cart", args=[self.flower.id])
        response = self.client.post(url)

        # Проверяем, что ответ успешный и товар добавлен в корзину
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(response.json()["quantity"], 1)

    def test_update_cart(self):
        """Тест обновления количества товара в корзине."""
        # Сначала добавляем товар в корзину
        self.client.post(reverse("add_to_cart", args=[self.flower.id]))

        # Обновляем количество товара
        url = reverse("update_cart", args=[self.flower.id, 2])
        response = self.client.post(url)

        # Проверяем, что ответ успешный и количество обновлено
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(response.json()["quantity"], 2)

    def test_view_cart(self):
        """Тест просмотра корзины."""
        # Добавляем товар в корзину
        self.client.post(reverse("add_to_cart", args=[self.flower.id]))

        # Получаем страницу корзины
        url = reverse("view_cart")
        response = self.client.get(url)

        # Проверяем, что страница загружена успешно и товар отображается
        self.assertEqual(response.status_code, 200)
        self.assertIn("Роза", response.content.decode())

    def test_remove_from_cart(self):
        """Тест удаления товара из корзины."""
        # Добавляем товар в корзину
        self.client.post(reverse("add_to_cart", args=[self.flower.id]))

        # Удаляем товар из корзины
        url = reverse("remove_from_cart", args=[self.flower.id])
        response = self.client.post(url)

        # Проверяем, что ответ успешный и товар удален
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)

    def test_clear_cart(self):
        """Тест очистки корзины."""
        # Добавляем товар в корзину
        self.client.post(reverse("add_to_cart", args=[self.flower.id]))

        # Очищаем корзину
        url = reverse("clear_cart")
        response = self.client.post(url)

        # Проверяем, что ответ успешный и корзина пуста
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)

    def test_checkout(self):
        """Тест оформления заказа."""
        # Проверяем, что пользователь авторизован
        login_success = self.client.login(username="testuser", password="testpass123")
        self.assertTrue(login_success, "Failed to log in user")

        # Добавляем товар в корзину через прямую модификацию сессии
        session = self.client.session
        session["cart"] = {str(self.flower.id): 1}
        session.save()

        # Убедимся, что корзина не пуста
        cart = self.client.session.get("cart", {})
        self.assertTrue(cart)

        # Оформляем заказ
        url = reverse("checkout")
        response = self.client.post(url, {"address": "ул. Ленина, 10"}, HTTP_X_TEST="true")

        # Выводим содержимое ответа для отладки
        print("Response content:", response.content.decode())

        # Проверяем, что ответ успешный и заказ оформлен
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)

        # Проверяем, что заказ сохранен в базе данных
        order = Order.objects.filter(user=self.profile).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, "awaiting_payment")
        self.assertEqual(order.address, "ул. Ленина, 10")

        # Проверяем, что элементы заказа сохранены
        order_items = OrderItem.objects.filter(order=order)
        self.assertEqual(order_items.count(), 1)
        self.assertEqual(order_items[0].flower, self.flower)
        self.assertEqual(order_items[0].quantity, 1)

        # Проверяем, что корзина очищена
        cart = self.client.session.get("cart", {})
        self.assertFalse(cart)

