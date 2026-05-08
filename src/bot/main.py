import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from database import get_user_by_phone, save_telegram_id

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_states = {}

@dp.message(CommandStart())
async def start(message: Message): #/start - просим вести номер телефона
    user_states[message.from_user.id] = 'waiting_phone'
    await message.answer(
        'Добро пожаловать! \n'
        'Введите ваш номер телефона.\n'
        'Формат: +000123456789'
    )
@dp.message(F.text)
async def handle_phone(message: Message): #Обрабатываем введенный номер телефона
    telegram_id = message.from_user.id

    #Проверяем состояние пользователя
    if user_states.get(telegram_id) != 'waiting_phone':
        await message.answer('Отправьте команду /start для начала.')
        return
    phone = message.text.strip()
    user = get_user_by_phone(phone) #Ищем пользователя по телефону

    if not user:
        await message.answer(
            'Пользователь с таким номером не найден.\n'
            'Проверьте номер и попробуйте снова.'
        )
        return
    save_telegram_id(user.id, telegram_id) #Сохраняем Telegram ID
    del user_states[telegram_id] #Убираем состояние
    await message.answer('Вы успешно зарегистрированы в системе!')

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
