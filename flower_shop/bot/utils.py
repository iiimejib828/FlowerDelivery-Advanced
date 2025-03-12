import asyncio
from aiogram import Bot
from bot.config import TOKEN

async def send_telegram_message(chat_id, text, reply_markup=None):
    bot = Bot(token=TOKEN)
    try:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")
    finally:
        await bot.session.close()

def send_message(chat_id, text, reply_markup=None):
    asyncio.run(send_telegram_message(chat_id, text, reply_markup))