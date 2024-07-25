# Импорт необходимых модулей и библиотек
from create_bot import dp  # Импорт объекта 'dp' из модуля 'create_bot'
from aiogram import types  # Импорт модуля 'types' из библиотеки 'aiogram'

# Обработчик сообщений, активирующийся при получении текстового сообщения "Контакты"
@dp.message_handler(lambda message: message.text == "Контакты")
async def contacts_handler(message: types.Message):
    await message.delete()  # Удаление исходного сообщения, содержащего команду "Контакты"

    # Текст с контактной информацией
    contacts_text = "<b>Адрес:</b> г. Москва, Ружейный переулок, 3\n" \
                    "<b>Тел:</b> +7 (968) 395-20-13\n" \
                    "<b>Часы работы:</b>\n" \
                    "Пн-Сб с 11:00 до 20:00\n" \
                    "Вс с 12:00 до 18:00\n" \
                    "<b>E-mail:</b> lombardmsc@yandex.ru\n" \
                    "<b>ООО Ломбард «Эксклюзив»</b>\n" \
                    "<b>ИНН:</b> 9704055436\n" \
                    "<b>ОГРН:</b> 1217700134288\n\n" \
                    "<b>Перейдите в</b> /menu <b>для доступа к другим функциям.</b>"

    map_url = "https://yandex.ru/maps/org/lombard_exclusive/56089976809/?ll=37.581774%2C55.742568&z=14"
    keyboard = types.InlineKeyboardMarkup()  # Создание клавиатуры для инлайн-кнопки
    map_button = types.InlineKeyboardButton(text="Открыть карту", url=map_url)  # Создание инлайн-кнопки "Открыть карту"
    keyboard.add(map_button)  # Добавление кнопки на клавиатуру

    # Отправка сообщения с контактной информацией и клавиатурой
    await message.answer(contacts_text, parse_mode="HTML", reply_markup=keyboard)