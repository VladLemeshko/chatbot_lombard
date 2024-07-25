from aiogram.dispatcher.filters.state import State, StatesGroup

# Создание общего состояния для фильтров
class FiltersStatePendants(StatesGroup):
    filter_selected_pendants = State()  # Общее состояние выбора фильтра
    filter_price_pendants = State()
    filter_brand_pendants = State()
    filter_condition_pendants = State()
    filter_gender_pendants = State()