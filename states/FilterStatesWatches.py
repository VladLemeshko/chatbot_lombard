from aiogram.dispatcher.filters.state import State, StatesGroup

# Создание общего состояния для фильтров
class FiltersState(StatesGroup):
    filter_selected = State()  # Общее состояние выбора фильтра
    filter_price = State()
    filter_brand = State()
    filter_condition = State()
    filter_gender = State()