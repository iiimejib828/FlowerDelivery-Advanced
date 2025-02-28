import asyncio
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup
from bot.config import TOKEN  # Подключаем ваш токен

loop = asyncio.get_event_loop()

# Инициализируем бота
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

async def send_telegram_message(chat_id: int, text: str, reply_markup: InlineKeyboardMarkup = None):
    """Асинхронная отправка сообщения в Telegram с поддержкой клавиатур."""
    try:
        await bot.send_message(chat_id, text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

def send_message(chat_id: int, text: str, reply_markup: InlineKeyboardMarkup = None):
    loop.run_until_complete(send_telegram_message(chat_id, text, reply_markup=reply_markup))


