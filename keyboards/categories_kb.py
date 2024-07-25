from aiogram.types import KeyboardButton, ReplyKeyboardMarkup



def get_categories_kb_class() -> ReplyKeyboardMarkup:
    kb_categories_class = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton("Швейцарские часы")],
        [KeyboardButton("Серьги"), KeyboardButton("Браслеты")],
        [KeyboardButton("Кольца"), KeyboardButton("Подвески")]],
        resize_keyboard=True)
    
    return kb_categories_class
