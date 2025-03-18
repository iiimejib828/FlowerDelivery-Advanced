import unittest
import asyncio
import django
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.db import connection
import pytest
import sys

# Настраиваем Django перед импортами моделей
if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'users',
            'orders',
            'catalog',
            'cart',
        ],
        AUTH_USER_MODEL='auth.User',
    )
    django.setup()

from asgiref.sync import sync_to_async
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from aiogram import types
from bot.main import start_command, process_contact, unlink_telegram, check_payment_reminders
from bot.utils import send_telegram_message
from users.models import UserProfile, notify_profile_update
from orders.models import Order, send_status_update
from cart.models import WorkingHours
from django.utils.timezone import now, timedelta
from freezegun import freeze_time
from datetime import time
from cart.views import is_working_hours

@pytest.mark.django_db
class TestBot(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if 'unittest' in sys.modules and 'pytest' not in sys.argv:
            connection.disable_constraint_checking()
            call_command('migrate', verbosity=0, interactive=False)
            connection.enable_constraint_checking()

    def setUp(self):
        post_save.disconnect(notify_profile_update, sender=UserProfile)
        post_save.disconnect(send_status_update, sender=Order)
        self.auth_user = User.objects.create(username="testuser")
        self.user, created = UserProfile.objects.get_or_create(user=self.auth_user)
        self.user.full_name = "Test User"
        self.user.phone = "+79991234567"
        self.user.telegram_id = 123456789
        self.user.address = "ул. Ленина, 10"
        self.user.save()
        self.fixed_time = now()
        self.order = Order.objects.create(
            user=self.user,
            status="awaiting_payment",
            total_price=1000.00
        )
        self.order.created_at = self.fixed_time - timedelta(hours=48)
        self.order.save()

        # Динамическое определение текущего дня недели
        days_of_week = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        current_day = days_of_week[self.fixed_time.weekday()]
        WorkingHours.objects.create(
            day=current_day,
            opening_time=time(0, 0),
            closing_time=time(23, 59),
            is_working=True
        )

    def tearDown(self):
        UserProfile.objects.all().delete()
        Order.objects.all().delete()
        User.objects.all().delete()
        WorkingHours.objects.all().delete()
        post_save.connect(notify_profile_update, sender=UserProfile)
        post_save.connect(send_status_update, sender=Order)

    def test_user_profile_str(self):
        self.assertEqual(str(self.user), "Test User")

    def test_order_str(self):
        self.assertEqual(str(self.order), f"Заказ {self.order.id} - Test User")

    def test_order_is_payment_overdue(self):
        with freeze_time(self.fixed_time):
            self.assertTrue(self.order.is_payment_overdue())
        new_order = Order.objects.create(
            user=self.user,
            status="awaiting_payment",
            total_price=500.00
        )
        new_order.created_at = self.fixed_time
        new_order.save()
        self.assertFalse(new_order.is_payment_overdue())

    @patch('bot.main.bot.send_message', new_callable=AsyncMock)
    async def test_start_command_registered_user(self, mock_send_message):
        message = Mock(spec=types.Message)
        message.from_user = Mock(id=123456789)
        message.chat = Mock(id=123456789)
        await start_command(message)
        mock_send_message.assert_called_once()
        call_args = mock_send_message.call_args[0]
        self.assertIn("👤 <b>Ваш профиль</b>", call_args[1])
        self.assertIn("Test User", call_args[1])
        self.assertIn("+79991234567", call_args[1])

    @patch('bot.main.bot.send_message', new_callable=AsyncMock)
    async def test_start_command_unregistered_user(self, mock_send_message):
        message = Mock(spec=types.Message)
        message.from_user = Mock(id=987654321)
        message.chat = Mock(id=987654321)
        await start_command(message)
        mock_send_message.assert_called_once()
        call_args = mock_send_message.call_args[0]
        self.assertIn("❌ Вы не зарегистрированы", call_args[1])

    @patch('bot.main.bot.send_message', new_callable=AsyncMock)
    async def test_process_contact_success(self, mock_send_message):
        message = Mock(spec=types.Message)
        message.from_user = Mock(id=987654321)
        message.chat = Mock(id=987654321)
        message.contact = Mock(phone_number="+79991234567")
        await process_contact(message)
        mock_send_message.assert_called_once_with(
            987654321,
            "✅ Ваш Telegram успешно привязан к аккаунту!"
        )
        updated_user = await sync_to_async(UserProfile.objects.get)(phone="+79991234567")
        self.assertEqual(updated_user.telegram_id, 987654321)

    @patch('bot.main.bot.send_message', new_callable=AsyncMock)
    async def test_process_contact_not_found(self, mock_send_message):
        message = Mock(spec=types.Message)
        message.from_user = Mock(id=987654321)
        message.chat = Mock(id=987654321)
        message.contact = Mock(phone_number="+79990000000")
        await process_contact(message)
        mock_send_message.assert_called_once()
        call_args = mock_send_message.call_args[0]
        self.assertIn("❌ Ошибка: UserProfile matching query does not exist", call_args[1])
        self.assertIn("+79990000000", call_args[1])

    @patch('bot.main.bot.send_message', new_callable=AsyncMock)
    async def test_unlink_telegram_success(self, mock_send_message):
        message = Mock(spec=types.Message)
        message.from_user = Mock(id=123456789)
        message.chat = Mock(id=123456789)
        await unlink_telegram(message)
        mock_send_message.assert_called_once_with(
            123456789,
            "✅ Ваш Telegram успешно отвязан от аккаунта."
        )
        updated_user = await sync_to_async(UserProfile.objects.get)(phone="+79991234567")
        self.assertIsNone(updated_user.telegram_id)

    @patch('bot.main.bot.send_message', new_callable=AsyncMock)
    @patch('cart.views.is_working_hours')
    @patch('orders.models.Order.objects.filter')
    @patch('orders.models.Order.is_payment_overdue')
    async def test_check_payment_reminders(self, mock_is_payment_overdue, mock_order_filter, mock_is_working_hours, mock_send_message):
        mock_is_payment_overdue.return_value = True
        mock_queryset = MagicMock()
        mock_queryset.select_related.return_value = [self.order]
        mock_order_filter.return_value = mock_queryset
        mock_is_working_hours.return_value = True
        
        self.assertTrue(await sync_to_async(is_working_hours)(), "is_working_hours should return True via sync_to_async")
        overdue_orders = mock_order_filter.return_value.select_related('user')
        self.assertEqual(len(overdue_orders), 1, "overdue_orders should contain one order")
        self.assertEqual(overdue_orders[0].id, self.order.id, "overdue_orders[0] should match self.order")
        self.assertTrue(await sync_to_async(overdue_orders[0].is_payment_overdue)(), "is_payment_overdue should return True")
        
        await check_payment_reminders()
        
        mock_send_message.assert_called_once_with(
            123456789,
            f"⚠️ Ваш заказ #{self.order.id} ожидает оплаты! Пожалуйста, оплатите его."
        )

    @patch('aiogram.Bot.send_message', new_callable=AsyncMock)
    async def test_send_telegram_message(self, mock_bot_send_message):
        chat_id = 123456789
        text = "Test message"
        await send_telegram_message(chat_id, text)
        mock_bot_send_message.assert_called_once_with(chat_id=chat_id, text=text, reply_markup=None)

    def test_run_async(self):
        async def dummy():
            return "done"
        result = asyncio.run(dummy())
        self.assertEqual(result, "done")

if __name__ == '__main__':
    unittest.main(verbosity=2)