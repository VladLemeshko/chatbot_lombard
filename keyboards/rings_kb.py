from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

for_whom_mapping = {
    "gender_male": "Мужские",
    "gender_female": "Женские",
    "gender_unisex": "Унисекс",
}

condition_mapping = {
    "condition_new": "Новые",
    "condition_like_new": "Как новые",
    "condition_used": "Б/У",
}

def create_filter_keyboard_rings(user_filters):
    min_price = user_filters.get('filter_price', {}).get('min_price')
    max_price = user_filters.get('filter_price', {}).get('max_price')
    price_text = f"{min_price}$-{max_price}$" if min_price is not None or max_price is not None else "Цена"

    gender = for_whom_mapping.get(user_filters.get('filter_gender', {}).get('gender', ''))
    gender_text = gender if gender else 'Пол'

    condition = condition_mapping.get(user_filters.get('filter_condition', {}).get('condition', ''))
    condition_text = condition if condition else 'Состояние'

    brand = user_filters.get('filter_brand', {}).get('brand')
    brand_text = f"{brand}" if brand else "Бренд"

    keyboard = InlineKeyboardMarkup(row_width=2)

    # Добавляем изначальные кнопки "Цена", "Бренд", "Состояние", "Пол"
    keyboard.add(
        InlineKeyboardButton(f"{price_text}", callback_data="filter_price_rings"),
        InlineKeyboardButton(f"{brand_text}", callback_data="filter_brand_rings"),
        InlineKeyboardButton(f"{condition_text}", callback_data="filter_condition_rings"),
        InlineKeyboardButton(f"{gender_text}", callback_data="filter_gender_rings")
    )

    # Кнопка "Сбросить фильтры"
    reset_button = InlineKeyboardButton("Сбросить фильтры", callback_data="reset_filters_rings")
    keyboard.add(reset_button)

    keyboard.add(InlineKeyboardButton("Поиск🔎", switch_inline_query_current_chat="rings"))

    return keyboard