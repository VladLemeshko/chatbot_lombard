from aiogram import types
from aiogram.types import Message, InputTextMessageContent, InlineQuery, InlineQueryResultArticle, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery
from create_bot import dp, bot  # Подставьте правильный импорт для вашего бота

# Импорт функций для работы с данными о часах
from catalogs.earrings_data.sqlite_earrings import get_all_earrings, get_filtered_earrings, get_price_range_earrings, get_total_earrings, get_earrings_data_by_id, get_unique_brands_earrings
from keyboards.coditiion_kb import condition_keyboard
from keyboards.gender_kb import gender_keyboard
from keyboards.earrings_kb import create_filter_keyboard_earrings
from data.users_sqlite import save_user_filter, get_user_filters, clear_user_filters
from states.FilterStatesEarrings import FiltersStateEarrings
from data.config import chat_id

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

user_filters = {
    'filter_price': {},
    'filter_brand': {},
    'filter_condition': {},
    'filter_gender': {},
}
    
# Изменения в обработчике фильтров
@dp.callback_query_handler(lambda query: query.data in ["filter_price_earrings", "filter_brand_earrings", "filter_condition_earrings", "filter_gender_earrings"], state="*")
async def apply_filter(query: CallbackQuery, state: FSMContext):
    await query.answer()
    filter_name = query.data.replace("filter_", "")  # Извлекаем имя фильтра из данных кнопки

    # Завершаем общее состояние выбора фильтра
    await FiltersStateEarrings.filter_selected_earrings.set()

    # Здесь мы сохраняем выбранный фильтр в состоянии (FSM)
    async with state.proxy() as data:
        data['filter'] = filter_name
    # Здесь вы можете добавить логику запроса необходимых данных у пользователя
    if filter_name == "price_earrings":
        min_price, max_price = await get_price_range_earrings()  # Получаем минимальную и максимальную цену из БД
        await query.message.answer(f"Введите диапазон цен в долларах (минимальная: {min_price}$ и максимальная: {max_price}$, например, 3000-15000):")
        await FiltersStateEarrings.filter_price_earrings.set()  # Устанавливаем состояние для ожидания ценового диапазона
        
    if filter_name == "brand_earrings":
        # Получаем уникальные бренды из базы данных
        unique_brands = await get_unique_brands_earrings()
        
        # Создаем кнопки для каждого бренда
        brand_buttons = [InlineKeyboardButton(text=brand, callback_data=f"select_brand_{brand}") for brand in unique_brands]
        
        rows = [brand_buttons[i:i + 2] for i in range(0, len(brand_buttons), 2)]
        
        # Добавляем кнопки в клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

        await query.message.answer("Выберите бренд:", reply_markup=keyboard)
        await FiltersStateEarrings.filter_brand_earrings.set()

                
    elif filter_name == "condition_earrings":
        await query.message.answer("Выберите состояние:", reply_markup=condition_keyboard)
        await FiltersStateEarrings.filter_condition_earrings.set()  # Устанавливаем состояние для ожидания состояния
    elif filter_name == "gender_earrings":
        await query.message.answer("Выберите пол:", reply_markup=gender_keyboard)
        await FiltersStateEarrings.filter_gender_earrings.set()  # Устанавливаем состояние для ожидания пола

@dp.message_handler(state=FiltersStateEarrings.filter_price_earrings)
async def process_price_range(message: Message, state: FSMContext):
    
    async with state.proxy() as data:
        try:
            min_price, max_price = map(int, message.text.split('-'))
            data['min_price'] = min_price
            data['max_price'] = max_price
        except ValueError:
            await message.reply("Некорректный формат ввода. Пожалуйста, введите диапазон цен в формате Мин-Макс, например, 100-500.")
            return

        price_filters = {
            'min_price': data['min_price'],
            'max_price': data['max_price']
        }

        user_id = message.from_user.id

        # Сохранение фильтров пользователя в базу данных
        await save_user_filter(user_id, 'filter_price', price_filters)

        keyboard = create_filter_keyboard_earrings(await get_user_filters(user_id))
        await message.answer("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()

# Шаг 6: Обработчик для фильтра "Бренд"
@dp.callback_query_handler(state=FiltersStateEarrings.filter_brand_earrings)
async def process_brand(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    async with state.proxy() as data:
        brand = callback_query.data.split("_", 2)[2]
        data['brand'] = brand

        user_id = callback_query.from_user.id

        # Сохранение фильтров пользователя в базу данных
        await save_user_filter(user_id, 'filter_brand', brand)

        # Создаем и обновляем клавиатуру с учетом выбранного бренда
        keyboard = create_filter_keyboard_earrings(await get_user_filters(user_id))
        await callback_query.message.edit_text("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()  # Завершаем состояние выбора бренда

# Шаг 6: Обработчик для фильтра "Состояние"
@dp.callback_query_handler(state=FiltersStateEarrings.filter_condition_earrings)
async def process_condition(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    async with state.proxy() as data:
        data['condition'] = callback_query.data

        user_id = callback_query.from_user.id

        # Сохранение фильтров пользователя в базу данных
        await save_user_filter(user_id, 'filter_condition', data['condition'])

        # Создаем и обновляем клавиатуру с учетом выбранного состояния
        keyboard = create_filter_keyboard_earrings(await get_user_filters(user_id))
        await callback_query.message.edit_text("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()  # Завершаем состояние выбора состояния

# Шаг 7: Обработчик для фильтра "Пол"
@dp.callback_query_handler(state=FiltersStateEarrings.filter_gender_earrings)
async def process_gender(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    async with state.proxy() as data:
        data['gender'] = callback_query.data

        user_id = callback_query.from_user.id

        # Сохранение фильтров пользователя в базу данных
        await save_user_filter(user_id, 'filter_gender', data['gender'])

        # Создаем и обновляем клавиатуру с учетом выбранного пола
        keyboard = create_filter_keyboard_earrings(await get_user_filters(user_id))
        await callback_query.message.edit_text("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()  # Завершаем состояние выбора пола
    
# Обработчик сброса фильтров
@dp.callback_query_handler(lambda callback_query: callback_query.data == 'reset_filters_earrings')
async def reset_filters(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    # Выполните сброс фильтров и очистите user_filters
    for key in user_filters:
        user_filters[key] = {}

    # Удалите данные о пользователе из базы данных
    await clear_user_filters(user_id)

    # Отправьте сообщение, уведомляющее пользователя о сбросе
    await bot.send_message(user_id, "Фильтры сброшены. Выберите другие новые фильтры для поиска серьг или нажмите поиск.", reply_markup=create_filter_keyboard_earrings(user_filters))


# Обработчик для инлайн-поиска
@dp.inline_handler(lambda query: query.query == "earrings")
async def search_inline_earrings(query: InlineQuery, state: FSMContext):
    user_id = query.from_user.id  # Получаем ID пользователя из запроса
    filters = await get_user_filters(user_id)

    print(filters)
    offset = int(query.offset) if query.offset else 0
    limit = 49  # Лимит на количество часов в одной порции
    next_offset = offset + limit  # Следующая позиция начала

    # Проверяем, есть ли выбранные фильтры, и выбираем соответствующую функцию для поиска
    if not filters:
        # Если фильтры не выбраны, используем get_all_earrings без ограничения
        filtered_earrings = await get_all_earrings(limit=limit, offset=offset)
    else:
        # Иначе используем get_filtered_earrings с выбранными фильтрами
        filtered_earrings = await get_filtered_earrings(filters, limit=limit, offset=offset)

    results = []
    for earrings in filtered_earrings:
        earrings_dict = {
            'id': earrings[0],
            'manufacture': earrings[1],
            'name': earrings[2],
            'price': earrings[3],
            'for_whom': for_whom_mapping.get(earrings[4], earrings[4]),
            'conditions': condition_mapping.get(earrings[5], earrings[5]),
            'images': earrings[6],  # Поле images является шестым полем (индекс 6)
            'characteristics': earrings[7]
        }

        # Проверяем, есть ли у часов название
        if not earrings_dict['name']:
            continue  # Пропускаем результаты без названия

        # Получаем первое изображение из списка изображений
        images_list = earrings_dict['images'].split(',')  # Если изображения разделены запятыми
        first_image = images_list[0].strip() if images_list else ''  # Получаем первое изображение

        # Создаем результаты инлайн-поиска для каждого товара
        title = earrings_dict['name']
        description = f"Цена: {earrings_dict['price']}, Бренд: {earrings_dict['manufacture']}, Состояние: {earrings_dict['conditions']}, Для кого: {earrings_dict['for_whom']}"
        input_message_content = InputTextMessageContent(f"Нажмите подробнее, чтобы увидеть все изображения и всю информацию о данном товаре")
        thumb_url = first_image  # URL первого изображения товара

        results.append(
            InlineQueryResultArticle(
                id=str(earrings_dict['id']),
                title=title,
                description=description,
                input_message_content=input_message_content,
                thumb_url=thumb_url,
                reply_markup=await create_earrings_inline_keyboard(earrings_dict['id'])  # Добавляем кнопку "Подробнее"
            )
        )

    if next_offset < await get_total_earrings():  # Если есть еще часы для отображения
        results.append(
            InlineQueryResultArticle(
                id='load_more',
                title='Загрузка...',
                input_message_content=InputTextMessageContent("Нажмите поиск снова"),
                thumb_url='https://png.pngtree.com/png-vector/20190817/ourlarge/pngtree-image-icon---vector-loading-download-and-upload-png-image_1694005.jpg'  # Замените на URL изображения кнопки
            )
        )

    await query.answer(
        results,
        cache_time=1,
        is_personal=True,
        next_offset=str(next_offset)  # Устанавливаем следующий offset
    )

async def create_earrings_inline_keyboard(earrings_id):
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton("Подробнее", callback_data=f"earrings_{earrings_id}")
    keyboard.add(button)
    return keyboard

# Обработчик нажатия на часы
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('earrings_'))
async def earrings_callback(query: CallbackQuery, state: FSMContext):
    # Извлекаем идентификатор часов из callback_data
    earrings_id = int(query.data.split('_')[1])

    # Получаем данные о часах по идентификатору (замените на ваш метод для получения данных о часах)
    earrings_data = await get_earrings_data_by_id(earrings_id)

    # Проверяем, что данные о часах найдены
    if earrings_data:
        # Разделяем данные о часах на отдельные элементы
        earrings_name = earrings_data[2]  # Извлекаем имя часов из кортежа
        earrings_manufacture = earrings_data[1]  # Извлекаем производителя из кортежа
        earrings_price = earrings_data[3]  # Извлекаем цену из кортежа
        earrings_for_whom_text = earrings_data[4]  # Извлекаем для кого из кортежа
        earrings_for_whom = for_whom_mapping.get(earrings_for_whom_text, earrings_for_whom_text)
        earrings_conditions_text = earrings_data[5]# Извлекаем состояние из кортежа
        earrings_conditions = condition_mapping.get(earrings_conditions_text, earrings_conditions_text)
        earrings_images = earrings_data[6].split(',')  # Если изображения разделены запятыми
        earrings_characteristics = earrings_data[7]  # Извлекаем характеристики из кортежа
        
        async with state.proxy() as data:
                    data['earrings_name'] = earrings_name
                    data['earrings_manufacture'] = earrings_manufacture
                    data['earrings_price'] = earrings_price
                    data['earrings_for_whom'] = earrings_for_whom
                    data['earrings_conditions'] = earrings_conditions
                    data['earrings_images'] = earrings_images
                    data['earrings_characteristics'] = earrings_characteristics
                    
        # Отправляем данные о часах пользователю
        message_text = f"Название: {earrings_name}\nПроизводитель: {earrings_manufacture}\nЦена: {earrings_price}\nДля кого: {earrings_for_whom}\nСостояние: {earrings_conditions}\n{earrings_characteristics}"
        await bot.send_message(chat_id=query.from_user.id, text=message_text)
        
        # Создаем обычную клавиатуру с двумя кнопками: "Назад" и "Я заинтересован данными часами"
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True,  selective=True, one_time_keyboard=True)
        keyboard.add(KeyboardButton("Назад к поиску серьг"))
        keyboard.add(KeyboardButton("Я заинтересован данными серьгами"))
        
        # Отправляем изображения часов пользователю
        for image_url in earrings_images:
            await bot.send_photo(chat_id=query.from_user.id, photo=image_url, reply_markup=keyboard)

    # Отмечаем callback_query как обработанный, чтобы избежать дополнительных нажатий
    await query.answer()

# Функция для обработки нажатия на кнопку "Я заинтересован данным товаром"
@dp.message_handler(lambda message: message.text == "Я заинтересован данными серьгами")
async def interested_in_product(message: types.Message, state: FSMContext):
    # Получаем данные о товаре из состояния FSM
    async with state.proxy() as data:
        earrings_name = data.get('earrings_name', 'N/A')
        earrings_manufacture = data.get('earrings_manufacture', 'N/A')
        earrings_price = data.get('earrings_price', 'N/A')
        earrings_for_whom = data.get('earrings_for_whom', 'N/A')
        earrings_conditions = data.get('earrings_conditions', 'N/A')
        earrings_images = data.get('earrings_images', [])
        earrings_characteristics = data.get('earrings_characteristics', 'N/A')
    
    # Получаем никнейм пользователя
    user_nickname = message.from_user.username or "Нет никнейма"

    # Формируем сообщение с данными о товаре и никнеймом пользователя
    message_text = f"Пользователь @{user_nickname} заинтересован в товаре:\n\n"
    message_text += f"Название: {earrings_name}\nПроизводитель: {earrings_manufacture}\nЦена: {earrings_price}\n"
    message_text += f"Для кого: {earrings_for_whom}\nСостояние: {earrings_conditions}\n"
    message_text += f"{earrings_characteristics}"

    # Отправляем только первое изображение в чат с определенным идентификатором (-612247085)
    if earrings_images:
        await bot.send_photo(chat_id=chat_id, photo=earrings_images[0], caption=message_text)

    # Отвечаем пользователю, что его интерес к товару передан
    await message.answer("Ваш интерес к товару передан. Мы свяжемся с вами для уточнения деталей.\n\nНажмите /menu, чтобы вернуться в главное меню.")