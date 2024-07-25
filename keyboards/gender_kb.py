from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Клавиатура для выбора пола
gender_keyboard = InlineKeyboardMarkup(row_width=3)
gender_buttons = [
    InlineKeyboardButton("Мужские", callback_data="gender_male"),
    InlineKeyboardButton("Женские", callback_data="gender_female"),
    InlineKeyboardButton("Унисекс", callback_data="gender_unisex"),
]
gender_keyboard.add(*gender_buttons)