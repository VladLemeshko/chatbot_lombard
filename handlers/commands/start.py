# Импорт необходимых модулей и библиотек
from create_bot import dp
from aiogram import types
from aiogram import exceptions

from data.users_sqlite import create_profile

# Обработчик команды "/start"
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    
    try:
        # Текст приветствия в формате HTML, который будет отправлен пользователю
        greeting = "Приветствую вас! Добро пожаловать в <em>Exclusive-watch.</em> \n\n" \
                "У нас вы найдете исключительно оригинальные, элитные швейцарские часы и ювелирные изделия по лучшим ценам." \
                "Мы имеем безупречную репутацию за 15 лет работы, а также осуществляем доставку товаров в любую точку России.\n\n" \
                "<b>Перейдите в</b> /menu <b>для доступа к дополнительным функциям.</b>"
        
        await message.answer(greeting, parse_mode="HTML")  # Отправка приветственного сообщения с форматированием HTML
        await create_profile(user_id=message.from_user.id)  # Вызов функции для создания профиля пользователя

    except exceptions.TelegramAPIError as e:
        print(f"Произошла ошибка Telegram API: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
