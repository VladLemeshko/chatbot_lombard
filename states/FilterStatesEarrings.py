from aiogram.dispatcher.filters.state import State, StatesGroup

# Создание общего состояния для фильтров
class FiltersStateEarrings(StatesGroup):
    filter_selected_earrings = State()  # Общее состояние выбора фильтра
    filter_price_earrings = State()
    filter_brand_earrings = State()
    filter_condition_earrings = State()
    filter_gender_earrings = State()