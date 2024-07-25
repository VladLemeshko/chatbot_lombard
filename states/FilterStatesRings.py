from aiogram.dispatcher.filters.state import State, StatesGroup

# Создание общего состояния для фильтров
class FiltersStateRings(StatesGroup):
    filter_selected_rings = State()  # Общее состояние выбора фильтра
    filter_price_rings = State()
    filter_brand_rings = State()
    filter_condition_rings = State()
    filter_gender_rings = State()