from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Клавиатура для выбора состояния
condition_keyboard = InlineKeyboardMarkup(row_width=3)
condition_buttons = [
    InlineKeyboardButton("Новые", callback_data="condition_new"),
    InlineKeyboardButton("Как новые", callback_data="condition_like_new"),
    InlineKeyboardButton("Б/У", callback_data="condition_used"),
]
condition_keyboard.add(*condition_buttons)