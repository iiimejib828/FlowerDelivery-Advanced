from django.urls import reverse, resolve
from .views import order_list, repeat_order, cancel_order
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from users.models import UserProfile
from catalog.models import Flower
from .models import Order, OrderItem
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class OrderUrlsTest(TestCase):
    def test_order_list_url(self):
        """Тест URL для списка заказов."""
        url = reverse("order_list")
        self.assertEqual(resolve(url).func, order_list)

    def test_repeat_order_url(self):
        """Тест URL для повторения заказа."""
        url = reverse("repeat_order", args=[1])
        self.assertEqual(resolve(url).func, repeat_order)

    def test_cancel_order_url(self):
        """Тест URL для отмены заказа."""
        url = reverse("cancel_order", args=[1])
        self.assertEqual(resolve(url).func, cancel_order)

class OrderViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123", email="test@example.com")
        # Используем get_or_create для создания профиля, если он еще не существует
        self.profile, created = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={
                'full_name': 'Test User',
                'phone': '+79991234567',
                'address': 'ул. Ленина, 10'
            }
        )
        self.flower = Flower.objects.create(name="Роза", price=500.00)
        self.order = Order.objects.create(user=self.profile, status="awaiting_payment", total_price=1000.00, address="ул. Ленина, 10")
        self.order_item = OrderItem.objects.create(order=self.order, flower=self.flower, quantity=2, price=500.00, subtotal=1000.00)

    def test_order_list_view(self):
        """Тест страницы списка заказов."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("order_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Заказ #")

    def test_repeat_order_view(self):
        """Тест повторения заказа."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("repeat_order", args=[self.order.id]))
        self.assertEqual(response.status_code, 302)  # Перенаправление на корзину
        self.assertIn("cart", self.client.session)

    def test_cancel_order_view(self):
        """Тест отмены заказа."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("cancel_order", args=[self.order.id]))
        self.assertEqual(response.status_code, 302)  # Перенаправление на список заказов
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "canceled")

class OrderModelTest(TestCase):
    def setUp(self):
        # Создаем пользователя
        self.user = User.objects.create_user(username="testuser", password="testpass123", email="test@example.com")

        # Используем get_or_create для создания профиля, если он еще не существует
        self.profile, created = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={
                'full_name': 'Test User',
                'phone': '+79991234567',
                'address': 'ул. Ленина, 10'
            }
        )

        # Создаем цветок
        self.flower = Flower.objects.create(name="Роза", price=500.00)

        # Создаем заказ
        self.order = Order.objects.create(
            user=self.profile,
            status="awaiting_payment",
            total_price=1000.00,
            address="ул. Ленина, 10"
        )

        # Создаем элемент заказа
        self.order_item = OrderItem.objects.create(
            order=self.order,
            flower=self.flower,
            quantity=2,
            price=500.00,
            subtotal=1000.00
        )

    def test_duplicate_order(self):
        """Тест метода duplicate_order."""
        # Создаем новый заказ на основе существующего
        new_order = self.order.duplicate_order()

        # Проверяем, что новый заказ создан для того же пользователя
        self.assertEqual(new_order.user, self.profile)

        # Проверяем, что статус нового заказа "awaiting_payment"
        self.assertEqual(new_order.status, "awaiting_payment")

        # Проверяем, что общая стоимость нового заказа совпадает с оригиналом
        self.assertEqual(new_order.total_price, 1000.00)

        # Проверяем, что адрес доставки нового заказа совпадает с оригиналом
        self.assertEqual(new_order.address, "ул. Ленина, 10")

        # Проверяем, что новый заказ содержит те же элементы, что и оригинал
        self.assertEqual(new_order.items.count(), 1)
        new_item = new_order.items.first()
        self.assertEqual(new_item.flower, self.flower)
        self.assertEqual(new_item.quantity, 2)
        self.assertEqual(new_item.price, 500.00)
        self.assertEqual(new_item.subtotal, 1000.00)

    def test_get_order_summary(self):
        """Тест метода get_order_summary."""
        summary = self.order.get_order_summary()
        self.assertIn("Заказ #", summary)
        self.assertIn("Роза x 2 - 1000.00 руб.", summary)
        self.assertIn("Общая стоимость: 1000.00 руб.", summary)
        self.assertIn("Адрес доставки: ул. Ленина, 10", summary)

    def test_is_payment_overdue(self):
        """Тест метода is_payment_overdue."""
        # Заказ только что создан, оплата не просрочена
        self.assertFalse(self.order.is_payment_overdue())

        # Устанавливаем дату создания заказа на 25 часов назад
        self.order.created_at = timezone.now() - timedelta(hours=25)
        self.order.save()
        self.assertTrue(self.order.is_payment_overdue())

    def test_order_creation(self):
        """Тест создания заказа."""
        self.assertEqual(self.order.user, self.profile)
        self.assertEqual(self.order.status, "awaiting_payment")
        self.assertEqual(self.order.total_price, 1000.00)
        self.assertEqual(self.order.address, "ул. Ленина, 10")

    def test_order_item_creation(self):
        """Тест создания элемента заказа."""
        self.assertEqual(self.order_item.order, self.order)
        self.assertEqual(self.order_item.flower, self.flower)
        self.assertEqual(self.order_item.quantity, 2)
        self.assertEqual(self.order_item.price, 500.00)
        self.assertEqual(self.order_item.subtotal, 1000.00)
