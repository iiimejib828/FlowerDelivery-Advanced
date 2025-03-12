import asyncio
import pytest
import time
from asgiref.sync import sync_to_async
from aiogram import Bot
from aiogram.types import Message, Contact, CallbackQuery
from django.test import TestCase
from django.contrib.auth.models import User
from users.models import UserProfile
from orders.models import Order, OrderItem
from catalog.models import Flower
from bot.main import start_command, process_contact, unlink_telegram, check_payment_reminders, cancel_order, confirm_cancel_order, cancel_no
from bot.config import TOKEN, ADMIN_IDS
from unittest.mock import AsyncMock, patch
from datetime import timedelta

# Указываем область действия цикла событий
pytestmark = pytest.mark.asyncio(scope="function")

@pytest.mark.django_db
class TestBot(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser', password='12345')
        cls.profile = UserProfile.objects.get(user=cls.user)
        cls.profile.phone = "+79991234567"
        cls.profile.telegram_id = 123456789
        cls.profile.full_name = "Test User"
        cls.profile.address = "Test Address"
        cls.profile.save()

        cls.admin_user = User.objects.create_user(username='admin', password='admin123')
        cls.admin_profile = UserProfile.objects.get(user=cls.admin_user)
        cls.admin_profile.phone = "+79990000000"
        cls.admin_profile.telegram_id = ADMIN_IDS[0]
        cls.admin_profile.full_name = "Admin User"
        cls.admin_profile.save()

        cls.flower = Flower.objects.create(name="Rose", price=100.00)
        cls.order = Order.objects.create(
            user=cls.profile,
            status="awaiting_payment",
            total_price=200.00,
            address="Test Address"
        )
        cls.order_item = OrderItem.objects.create(
            order=cls.order,
            flower=cls.flower,
            quantity=2,
            price=100.00,
            subtotal=200.00
        )
        cls.bot = Bot(token=TOKEN)

    @pytest.fixture(autouse=True)
    async def setup_bot(self, monkeypatch):
        # Мокаем методы bot на уровне модуля bot.main
        with patch('bot.main.bot.send_message', new_callable=AsyncMock) as mock_send:
            with patch('bot.main.bot.edit_message_text', new_callable=AsyncMock) as mock_edit:
                with patch('bot.main.bot.answer_callback_query', new_callable=AsyncMock) as mock_answer:
                    self.bot_send_message = mock_send
                    self.bot_edit_message_text = mock_edit
                    self.bot_answer_callback_query = mock_answer
                    yield
        # Закрываем сессию после каждого теста
        await self.bot.session.close()

    async def test_start_command_with_profile(self):
        message = Message(
            message_id=1,
            date=int(time.time()),
            chat={"id": 123456789, "type": "private"},
            from_user={"id": 123456789, "is_bot": False, "first_name": "Test"}
        )
        with patch('users.models.UserProfile.get_by_telegram_id', return_value=self.profile):
            await start_command(message)
            self.bot_send_message.assert_called_once()
            call_args = self.bot_send_message.call_args
            assert call_args[0][0] == 123456789
            assert "Ваш профиль" in call_args[0][1]
            assert "Test User" in call_args[0][1]
            assert "+79991234567" in call_args[0][1]
            assert "Test Address" in call_args[0][1]

    async def test_start_command_without_profile(self):
        message = Message(
            message_id=1,
            date=int(time.time()),
            chat={"id": 987654321, "type": "private"},
            from_user={"id": 987654321, "is_bot": False, "first_name": "Unknown"}
        )
        with patch('users.models.UserProfile.get_by_telegram_id', return_value=None):
            await start_command(message)
            self.bot_send_message.assert_called_once()
            call_args = self.bot_send_message.call_args
            assert call_args[0][0] == 987654321
            assert "Вы не зарегистрированы" in call_args[0][1]

    async def test_process_contact_success(self):
        self.profile.telegram_id = None
        await sync_to_async(self.profile.save)()
        
        message = Message(
            message_id=1,
            date=int(time.time()),
            chat={"id": 987654321, "type": "private"},
            from_user={"id": 987654321, "is_bot": False, "first_name": "New"},
            contact=Contact(phone_number="+79991234567", user_id=987654321, first_name="New")
        )
        await process_contact(message)
        self.bot_send_message.assert_called_once_with(
            987654321,
            "✅ Ваш Telegram успешно привязан к аккаунту!"
        )
        profile = await sync_to_async(UserProfile.objects.get)(phone="+79991234567")
        assert profile.telegram_id == 987654321

    async def test_unlink_telegram(self):
        message = Message(
            message_id=1,
            date=int(time.time()),
            chat={"id": 123456789, "type": "private"},
            from_user={"id": 123456789, "is_bot": False, "first_name": "Test"}
        )
        await unlink_telegram(message)
        self.bot_send_message.assert_called_once_with(
            123456789,
            "✅ Ваш Telegram успешно отвязан от аккаунта."
        )
        self.profile.refresh_from_db()
        assert self.profile.telegram_id is None

    async def test_check_payment_reminders(self):
        self.order.created_at = self.order.created_at - timedelta(hours=25)
        await sync_to_async(self.order.save)()
        with patch('cart.views.is_working_hours', return_value=True):
            with patch('orders.models.Order.is_payment_overdue', return_value=True):
                await check_payment_reminders()
                self.bot_send_message.assert_called_once_with(
                    123456789,
                    f"⚠️ Ваш заказ #{self.order.id} ожидает оплаты! Пожалуйста, оплатите его."
                )

    async def test_cancel_order(self):
        callback = CallbackQuery(
            id="1",
            from_user={"id": 123456789, "is_bot": False, "first_name": "Test"},
            message=Message(
                message_id=1,
                date=int(time.time()),
                chat={"id": 123456789, "type": "private"},
                text="Test"
            ),
            data=f"cancel_order_{self.order.id}",
            chat_instance="test_chat_instance"
        )
        await cancel_order(callback)
        self.bot_edit_message_text.assert_called_once()
        call_args = self.bot_edit_message_text.call_args
        assert "Вы уверены, что хотите отменить заказ" in call_args[0][0]
        self.bot_answer_callback_query.assert_called_once_with("1")

    async def test_confirm_cancel_order(self):
        callback = CallbackQuery(
            id="1",
            from_user={"id": 123456789, "is_bot": False, "first_name": "Test"},
            message=Message(
                message_id=1,
                date=int(time.time()),
                chat={"id": 123456789, "type": "private"},
                text="Test"
            ),
            data=f"confirm_cancel_{self.order.id}",
            chat_instance="test_chat_instance"
        )
        await confirm_cancel_order(callback)
        self.order.refresh_from_db()
        assert self.order.status == "canceled"
        self.bot_edit_message_text.assert_called_once()
        call_args = self.bot_edit_message_text.call_args
        assert "Заказ отменен" in call_args[0][0]
        self.bot_answer_callback_query.assert_called_once_with("1", "Заказ отменен.")

    async def test_cancel_no(self):
        callback = CallbackQuery(
            id="1",
            from_user={"id": 123456789, "is_bot": False, "first_name": "Test"},
            message=Message(
                message_id=1,
                date=int(time.time()),
                chat={"id": 123456789, "type": "private"},
                text="Test"
            ),
            data=f"cancel_no_{self.order.id}",
            chat_instance="test_chat_instance"
        )
        await cancel_no(callback)
        self.bot_edit_message_text.assert_called_once()
        call_args = self.bot_edit_message_text.call_args
        assert "Отменить заказ" in str(call_args[1]['reply_markup'])
        self.bot_answer_callback_query.assert_called_once_with("1", "Отмена заказа отклонена.")
