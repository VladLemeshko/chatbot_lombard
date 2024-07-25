from aiogram import types
from aiogram.types import Message, InputTextMessageContent, InlineQuery, InlineQueryResultArticle, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery
from create_bot import dp, bot  # Подставьте правильный импорт для вашего бота

# Импорт функций для работы с данными о часах
from catalogs.watches_data.sqlite_watches import get_all_watches, get_filtered_watches, get_price_range, get_total_watches, get_watch_data_by_id, get_unique_brands
from keyboards.coditiion_kb import condition_keyboard
from keyboards.gender_kb import gender_keyboard
from keyboards.watches_kb import create_filter_keyboard
from data.users_sqlite import save_user_filter, get_user_filters, clear_user_filters
from states.FilterStatesWatches import FiltersState
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
@dp.callback_query_handler(lambda query: query.data in ["filter_price", "filter_brand", "filter_condition", "filter_gender"], state="*")
async def apply_filter(query: CallbackQuery, state: FSMContext):
    await query.answer()
    filter_name = query.data.replace("filter_", "")  # Извлекаем имя фильтра из данных кнопки

    # Завершаем общее состояние выбора фильтра
    await FiltersState.filter_selected.set()

    # Здесь мы сохраняем выбранный фильтр в состоянии (FSM)
    async with state.proxy() as data:
        data['filter'] = filter_name
    print(data)
    # Здесь вы можете добавить логику запроса необходимых данных у пользователя
    if filter_name == "price":
        min_price, max_price = await get_price_range()  # Получаем минимальную и максимальную цену из БД
        await query.message.answer(f"Введите диапазон цен в долларах (минимальная: {min_price}$ и максимальная: {max_price}$, например, 3000-15000):")
        await FiltersState.filter_price.set()  # Устанавливаем состояние для ожидания ценового диапазона
        
    if filter_name == "brand":
        # Получаем уникальные бренды из базы данных
        unique_brands = await get_unique_brands()
        
        # Создаем кнопки для каждого бренда
        brand_buttons = [InlineKeyboardButton(text=brand, callback_data=f"select_brand_{brand}") for brand in unique_brands]
        
        rows = [brand_buttons[i:i + 2] for i in range(0, len(brand_buttons), 2)]
        
        # Добавляем кнопки в клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

        await query.message.answer("Выберите бренд:", reply_markup=keyboard)
        await FiltersState.filter_brand.set()

                
    elif filter_name == "condition":
        await query.message.answer("Выберите состояние:", reply_markup=condition_keyboard)
        await FiltersState.filter_condition.set()  # Устанавливаем состояние для ожидания состояния
    elif filter_name == "gender":
        await query.message.answer("Выберите пол:", reply_markup=gender_keyboard)
        await FiltersState.filter_gender.set()  # Устанавливаем состояние для ожидания пола

@dp.message_handler(state=FiltersState.filter_price)
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

        keyboard = create_filter_keyboard(await get_user_filters(user_id))
        await message.answer("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()

# Шаг 6: Обработчик для фильтра "Бренд"
@dp.callback_query_handler(state=FiltersState.filter_brand)
async def process_brand(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    async with state.proxy() as data:
        brand = callback_query.data.split("_", 2)[2]
        data['brand'] = brand

        user_id = callback_query.from_user.id

        # Сохранение фильтров пользователя в базу данных
        await save_user_filter(user_id, 'filter_brand', brand)

        # Создаем и обновляем клавиатуру с учетом выбранного бренда
        keyboard = create_filter_keyboard(await get_user_filters(user_id))
        await callback_query.message.edit_text("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()  # Завершаем состояние выбора бренда

# Шаг 6: Обработчик для фильтра "Состояние"
@dp.callback_query_handler(state=FiltersState.filter_condition)
async def process_condition(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    async with state.proxy() as data:
        data['condition'] = callback_query.data

        user_id = callback_query.from_user.id

        # Сохранение фильтров пользователя в базу данных
        await save_user_filter(user_id, 'filter_condition', data['condition'])

        # Создаем и обновляем клавиатуру с учетом выбранного состояния
        keyboard = create_filter_keyboard(await get_user_filters(user_id))
        await callback_query.message.edit_text("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()  # Завершаем состояние выбора состояния

# Шаг 7: Обработчик для фильтра "Пол"
@dp.callback_query_handler(state=FiltersState.filter_gender)
async def process_gender(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    async with state.proxy() as data:
        data['gender'] = callback_query.data

        user_id = callback_query.from_user.id

        # Сохранение фильтров пользователя в базу данных
        await save_user_filter(user_id, 'filter_gender', data['gender'])

        # Создаем и обновляем клавиатуру с учетом выбранного пола
        keyboard = create_filter_keyboard(await get_user_filters(user_id))
        await callback_query.message.edit_text("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()  # Завершаем состояние выбора пола
    
# Обработчик сброса фильтров
@dp.callback_query_handler(lambda callback_query: callback_query.data == 'reset_filters')
async def reset_filters(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    # Выполните сброс фильтров и очистите user_filters
    for key in user_filters:
        user_filters[key] = {}

    # Удалите данные о пользователе из базы данных
    await clear_user_filters(user_id)

    # Отправьте сообщение, уведомляющее пользователя о сбросе
    await bot.send_message(user_id, "Фильтры сброшены. Выберите другие новые фильтры для поиска часов или нажмите поиск.", reply_markup=create_filter_keyboard(user_filters))


# Обработчик для инлайн-поиска
@dp.inline_handler(lambda query: query.query == "watches")
async def search_inline(query: InlineQuery, state: FSMContext):
    user_id = query.from_user.id  # Получаем ID пользователя из запроса
    filters = await get_user_filters(user_id)

    print(filters)
    offset = int(query.offset) if query.offset else 0
    limit = 49  # Лимит на количество часов в одной порции
    next_offset = offset + limit  # Следующая позиция начала

    # Проверяем, есть ли выбранные фильтры, и выбираем соответствующую функцию для поиска
    if not filters:
        # Если фильтры не выбраны, используем get_all_watches без ограничения
        filtered_watches = await get_all_watches(limit=limit, offset=offset)
    else:
        # Иначе используем get_filtered_watches с выбранными фильтрами
        filtered_watches = await get_filtered_watches(filters, limit=limit, offset=offset)

    results = []
    for watch in filtered_watches:
        watch_dict = {
            'id': watch[0],
            'manufacture': watch[1],
            'name': watch[2],
            'price': watch[3],
            'for_whom': for_whom_mapping.get(watch[4], watch[4]),
            'conditions': condition_mapping.get(watch[5], watch[5]),
            'images': watch[6],  # Поле images является шестым полем (индекс 6)
            'characteristics': watch[7]
        }

        # Проверяем, есть ли у часов название
        if not watch_dict['name']:
            continue  # Пропускаем результаты без названия

        # Получаем первое изображение из списка изображений
        images_list = watch_dict['images'].split(',')  # Если изображения разделены запятыми
        first_image = images_list[0].strip() if images_list else ''  # Получаем первое изображение

        # Создаем результаты инлайн-поиска для каждого товара
        title = watch_dict['name']
        description = f"Цена: {watch_dict['price']}, Бренд: {watch_dict['manufacture']}, Состояние: {watch_dict['conditions']}, Для кого: {watch_dict['for_whom']}"
        input_message_content = InputTextMessageContent(f"Нажмите подробнее, чтобы увидеть все изображения и всю информацию о данном товаре")
        thumb_url = first_image  # URL первого изображения товара

        results.append(
            InlineQueryResultArticle(
                id=str(watch_dict['id']),
                title=title,
                description=description,
                input_message_content=input_message_content,
                thumb_url=thumb_url,
                reply_markup=await create_watch_inline_keyboard(watch_dict['id'])  # Добавляем кнопку "Подробнее"
            )
        )

    if next_offset < await get_total_watches():  # Если есть еще часы для отображения
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

async def create_watch_inline_keyboard(watch_id):
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton("Подробнее", callback_data=f"watch_{watch_id}")
    keyboard.add(button)
    return keyboard

# Обработчик нажатия на часы
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('watch_'))
async def watch_callback(query: CallbackQuery, state: FSMContext):
    # Извлекаем идентификатор часов из callback_data
    watch_id = int(query.data.split('_')[1])

    # Получаем данные о часах по идентификатору (замените на ваш метод для получения данных о часах)
    watch_data = await get_watch_data_by_id(watch_id)

    # Проверяем, что данные о часах найдены
    if watch_data:
        # Разделяем данные о часах на отдельные элементы
        watch_name = watch_data[2]  # Извлекаем имя часов из кортежа
        watch_manufacture = watch_data[1]  # Извлекаем производителя из кортежа
        watch_price = watch_data[3]  # Извлекаем цену из кортежа
        watch_for_whom_text = watch_data[4]  # Извлекаем для кого из кортежа
        watch_for_whom = for_whom_mapping.get(watch_for_whom_text, watch_for_whom_text)
        watch_conditions_text = watch_data[5]# Извлекаем состояние из кортежа
        watch_conditions = condition_mapping.get(watch_conditions_text, watch_conditions_text)
        watch_images = watch_data[6].split(',')  # Если изображения разделены запятыми
        watch_characteristics = watch_data[7]  # Извлекаем характеристики из кортежа
        
        async with state.proxy() as data:
                    data['watch_name'] = watch_name
                    data['watch_manufacture'] = watch_manufacture
                    data['watch_price'] = watch_price
                    data['watch_for_whom'] = watch_for_whom
                    data['watch_conditions'] = watch_conditions
                    data['watch_images'] = watch_images
                    data['watch_characteristics'] = watch_characteristics
                    
        # Отправляем данные о часах пользователю
        message_text = f"Название: {watch_name}\nПроизводитель: {watch_manufacture}\nЦена: {watch_price}\nДля кого: {watch_for_whom}\nСостояние: {watch_conditions}\n{watch_characteristics}"
        await bot.send_message(chat_id=query.from_user.id, text=message_text)
        
        # Создаем обычную клавиатуру с двумя кнопками: "Назад" и "Я заинтересован данными часами"
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True,  selective=True, one_time_keyboard=True)
        keyboard.add(KeyboardButton("Назад к поиску часов"))
        keyboard.add(KeyboardButton("Я заинтересован данными часами"))
        
        # Отправляем изображения часов пользователю
        for image_url in watch_images:
            await bot.send_photo(chat_id=query.from_user.id, photo=image_url, reply_markup=keyboard)

    # Отмечаем callback_query как обработанный, чтобы избежать дополнительных нажатий
    await query.answer()

# Функция для обработки нажатия на кнопку "Я заинтересован данным товаром"
@dp.message_handler(lambda message: message.text == "Я заинтересован данными часами")
async def interested_in_product(message: types.Message, state: FSMContext):
    # Получаем данные о товаре из состояния FSM
    async with state.proxy() as data:
        watch_name = data.get('watch_name', 'N/A')
        watch_manufacture = data.get('watch_manufacture', 'N/A')
        watch_price = data.get('watch_price', 'N/A')
        watch_for_whom = data.get('watch_for_whom', 'N/A')
        watch_conditions = data.get('watch_conditions', 'N/A')
        watch_images = data.get('watch_images', [])
        watch_characteristics = data.get('watch_characteristics', 'N/A')
    
    # Получаем никнейм пользователя
    user_nickname = message.from_user.username or "Нет никнейма"

    # Формируем сообщение с данными о товаре и никнеймом пользователя
    message_text = f"Пользователь @{user_nickname} заинтересован в товаре:\n\n"
    message_text += f"Название: {watch_name}\nПроизводитель: {watch_manufacture}\nЦена: {watch_price}\n"
    message_text += f"Для кого: {watch_for_whom}\nСостояние: {watch_conditions}\n"
    message_text += f"{watch_characteristics}"

    # Отправляем только первое изображение в чат с определенным идентификатором (-612247085)
    if watch_images:
        await bot.send_photo(chat_id=chat_id, photo=watch_images[0], caption=message_text)

    # Отвечаем пользователю, что его интерес к товару передан
    await message.answer("Ваш интерес к товару передан. Мы свяжемся с вами для уточнения деталей.\n\nНажмите /menu, чтобы вернуться в главное меню.")