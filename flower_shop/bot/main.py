import asyncio
from asgiref.sync import sync_to_async
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from django.core.exceptions import ObjectDoesNotExist
from orders.models import Order  # Убрали ненужный импорт User
from aiogram.client.default import DefaultBotProperties
from bot.config import TOKEN, ADMIN_IDS
from aiogram.types import CallbackQuery
from cart.views import is_working_hours
from users.models import UserProfile

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()

# Клавиатура для запроса номера телефона
phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📞 Отправить номер", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Показывает Telegram ID пользователя"""
    telegram_id = message.from_user.id
    profile = await sync_to_async(UserProfile.get_by_telegram_id)(telegram_id)

    if profile:
        response_text = (
            f"👤 <b>Ваш профиль</b>\n"
            f"📍 Telegram ID: <code>{telegram_id}</code>\n"
            f"👤 Имя: {profile.full_name}\n"
            f"📞 Телефон: {profile.phone or 'Не указан'}\n"
            f"📍 Адрес: {profile.address or 'Не указан'}"
        )
    else:
        response_text = (
            f"⚠️ Ваш Telegram ID: <code>{telegram_id}</code>\n\n"
            "❌ Вы не зарегистрированы в системе. "
            "Отправьте ваш номер телефона для привязки к профилю."
        )

    await message.answer(response_text, reply_markup=phone_keyboard)

@dp.message(lambda message: message.contact)
async def process_contact(message: types.Message):
    """Привязка Telegram ID к аккаунту по номеру телефона"""
    phone_number = message.contact.phone_number.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if phone_number.startswith("8"):
        phone_number = "+7" + phone_number[1:]
    elif phone_number.startswith("7"):
        phone_number = "+" + phone_number

    try:
        profile = await sync_to_async(UserProfile.objects.get)(phone=phone_number)
        if profile:
            profile.telegram_id = message.from_user.id
            await sync_to_async(profile.save)()
            await message.answer("✅ Ваш Telegram успешно привязан к аккаунту!")
        else:
            await message.answer(f"❌ Ошибка: пользователь с номером телефона {phone_number} не найден. Проверьте корректность номера.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}\nномер телефона {phone_number}")

@dp.message(Command("unlink"))
async def unlink_telegram(message: types.Message):
    """Отвязка Telegram ID от пользователя"""
    try:
        user = await sync_to_async(UserProfile.objects.get)(telegram_id=message.from_user.id)
        user.telegram_id = None
        await sync_to_async(user.save)()
        await message.answer("✅ Ваш Telegram успешно отвязан от аккаунта.")
    except ObjectDoesNotExist:
        await message.answer("❌ Ошибка: ваш Telegram ID не привязан к аккаунту.")

@dp.message(Command("admin_link"))
async def admin_link_user(message: types.Message):
    """Администратор привязывает Telegram ID к пользователю"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return

    args = message.text.split()
    if len(args) != 3:
        await message.answer("Используйте: `/admin_link <номер_телефона> <telegram_id>`")
        return

    phone_number, telegram_id = args[1], args[2]

    try:
        user = await sync_to_async(UserProfile.objects.get)(phone=phone_number)
        user.telegram_id = telegram_id
        await sync_to_async(user.save)()
        await message.answer(f"✅ Telegram ID {telegram_id} успешно привязан к пользователю {phone_number}.")
    except ObjectDoesNotExist:
        await message.answer("❌ Ошибка: пользователь с таким номером телефона не найден.")

@dp.message(Command("admin_unlink"))
async def admin_unlink_user(message: types.Message):
    """Администратор отвязывает Telegram ID от пользователя"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("Используйте: `/admin_unlink <номер_телефона>`")
        return

    phone_number = args[1]

    try:
        user = await sync_to_async(UserProfile.objects.get)(phone=phone_number)
        user.telegram_id = None
        await sync_to_async(user.save)()
        await message.answer(f"✅ Telegram ID успешно отвязан от пользователя {phone_number}.")
    except ObjectDoesNotExist:
        await message.answer("❌ Ошибка: пользователь с таким номером телефона не найден.")

async def send_payment_reminders():
    """Периодически проверяет заказы и отправляет напоминания об оплате"""
    while True:
        await asyncio.sleep(10800)  # Проверяем раз в три часа
        if not await sync_to_async(is_working_hours)():
            continue
        overdue_orders = await sync_to_async(list)(Order.objects.filter(status="awaiting_payment").select_related('user'))
        for order in overdue_orders:
            is_overdue = await sync_to_async(order.is_payment_overdue)()
            if not hasattr(order, 'user') or not order.user:
                for admin_id in ADMIN_IDS:
                    await bot.send_message(
                        admin_id,
                        f"⚠️ Заказ #{order.id} пропущен: отсутствует пользователь"
                    )
                    print(f"Заказ #{order.id} пропущен: отсутствует пользователь, уведомлен админ")
                continue
            
            if is_overdue:
                if order.user.telegram_id:
                    await bot.send_message(
                        order.user.telegram_id,
                        f"⚠️ Ваш заказ #{order.id} ожидает оплаты! Пожалуйста, оплатите его."
                    )
                    print(f"Уведомление отправлено пользователю для заказа #{order.id}")
                else:
                    # Уведомляем админа, если telegram_id отсутствует
                    for admin_id in ADMIN_IDS:
                        await bot.send_message(
                            admin_id,
                            f"⚠️ Заказ #{order.id} просрочен, но у пользователя {order.user.full_name} (телефон: {order.user.phone}) нет telegram_id."
                        )
                    print(f"Заказ #{order.id} пропущен: отсутствует telegram_id, уведомлен админ")

@dp.callback_query(lambda callback: callback.data.startswith("cancel_order_"))
async def cancel_order(callback: CallbackQuery):
    """Обработка нажатия на кнопку 'Отменить заказ' с подтверждением."""
    order_id = int(callback.data.split("_")[-1])
    order = await sync_to_async(Order.objects.get)(id=order_id)

    if order.status not in ["shipped", "delivered", "canceled"]:
        # Запрашиваем подтверждение
        confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Да, отменить", callback_data=f"confirm_cancel_{order_id}")],
            [InlineKeyboardButton(text="Нет", callback_data=f"cancel_no_{order_id}")]
        ])
        await callback.message.edit_text(
            f"Вы уверены, что хотите отменить заказ #{order_id}?\n\n{await sync_to_async(order.get_order_summary)()}",
            reply_markup=confirm_keyboard
        )
        await callback.answer()
    else:
        await callback.message.edit_text(
            f"❌ Заказ #{order_id}:\n\n{await sync_to_async(order.get_order_summary)()}",
            reply_markup=None  # Убираем кнопки
        )
        await callback.answer("❌ Невозможно отменить заказ: он уже отправлен, доставлен или отменён.")

@dp.callback_query(lambda callback: callback.data.startswith("confirm_cancel_"))
async def confirm_cancel_order(callback: CallbackQuery):
    """Подтверждение отмены заказа."""
    order_id = int(callback.data.split("_")[-1])
    order = await sync_to_async(Order.objects.get)(id=order_id)

    if order.status not in ["shipped", "delivered", "canceled"]:
        order.status = "canceled"
        await sync_to_async(order.save)()
        await callback.message.edit_text(
            f"❌ Заказ #{order_id} отменен.\n\n{await sync_to_async(order.get_order_summary)()}",
            reply_markup=None  # Убираем кнопки
        )
        await callback.answer("Заказ отменен.")
    else:
        await callback.answer("❌ Невозможно отменить заказ: он уже отправлен или доставлен.")

@dp.callback_query(lambda callback: callback.data.startswith("cancel_no_"))
async def cancel_no(callback: CallbackQuery):
    """Отказ от отмены заказа."""
    order_id = int(callback.data.split("_")[-1])
    order = await sync_to_async(Order.objects.get)(id=order_id)
    order_summary = await sync_to_async(order.get_order_summary)()
    
    # Возвращаем исходное сообщение с кнопкой "Отменить"
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отменить заказ", callback_data=f"cancel_order_{order_id}")]
    ])
    reply_markup=cancel_keyboard if order.status in ["awaiting_payment", "pending", "processing"] else None
    await callback.message.edit_text(
        text=order_summary,
        reply_markup=reply_markup
    )
    await callback.answer("Отмена заказа отклонена.")

async def main():
    """Запуск бота"""
    asyncio.create_task(send_payment_reminders())  # Запускаем фоновую задачу
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())