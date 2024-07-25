from aiogram.dispatcher.filters.state import State, StatesGroup

# Создание общего состояния для фильтров
class FiltersStateBraclets(StatesGroup):
    filter_selected_braclets = State()  # Общее состояние выбора фильтра
    filter_price_braclets = State()
    filter_brand_braclets = State()
    filter_condition_braclets = State()
    filter_gender_braclets = State()