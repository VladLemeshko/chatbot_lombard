from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_menu_kb_class() -> ReplyKeyboardMarkup:
    kb_menu_class = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton("Каталог")],
        [KeyboardButton("Контакты")]],
        resize_keyboard=True)
    
    return kb_menu_class