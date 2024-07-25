from aiogram import types
from aiogram.types import Message, InputTextMessageContent, InlineQuery, InlineQueryResultArticle, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery
from create_bot import dp, bot  # Подставьте правильный импорт для вашего бота

# Импорт функций для работы с данными о часах
from catalogs.pendants_data.sqlite_pendants import get_all_pendants, get_filtered_pendants, get_price_range_pendants, get_total_pendants, get_pendants_data_by_id, get_unique_brands_pendants
from keyboards.coditiion_kb import condition_keyboard
from keyboards.gender_kb import gender_keyboard
from keyboards.pendants_kb import create_filter_keyboard_pendants
from data.users_sqlite import save_user_filter, get_user_filters, clear_user_filters
from states.FilterStatesPendants import FiltersStatePendants
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
@dp.callback_query_handler(lambda query: query.data in ["filter_price_pendants", "filter_brand_pendants", "filter_condition_pendants", "filter_gender_pendants"], state="*")
async def apply_filter(query: CallbackQuery, state: FSMContext):
    await query.answer()
    filter_name = query.data.replace("filter_", "")  # Извлекаем имя фильтра из данных кнопки

    # Завершаем общее состояние выбора фильтра
    await FiltersStatePendants.filter_selected_pendants.set()

    # Здесь мы сохраняем выбранный фильтр в состоянии (FSM)
    async with state.proxy() as data:
        data['filter'] = filter_name
    print(data)
    # Здесь вы можете добавить логику запроса необходимых данных у пользователя
    if filter_name == "price_pendants":
        min_price, max_price = await get_price_range_pendants()  # Получаем минимальную и максимальную цену из БД
        await query.message.answer(f"Введите диапазон цен в долларах (минимальная: {min_price}$ и максимальная: {max_price}$, например, 3000-15000):")
        await FiltersStatePendants.filter_price_pendants.set()  # Устанавливаем состояние для ожидания ценового диапазона
        
    if filter_name == "brand_pendants":
        # Получаем уникальные бренды из базы данных
        unique_brands = await get_unique_brands_pendants()
        
        # Создаем кнопки для каждого бренда
        brand_buttons = [InlineKeyboardButton(text=brand, callback_data=f"select_brand_{brand}") for brand in unique_brands]
        
        rows = [brand_buttons[i:i + 2] for i in range(0, len(brand_buttons), 2)]
        
        # Добавляем кнопки в клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

        await query.message.answer("Выберите бренд:", reply_markup=keyboard)
        await FiltersStatePendants.filter_brand_pendants.set()

                
    elif filter_name == "condition_pendants":
        await query.message.answer("Выберите состояние:", reply_markup=condition_keyboard)
        await FiltersStatePendants.filter_condition_pendants.set()  # Устанавливаем состояние для ожидания состояния
    elif filter_name == "gender_pendants":
        await query.message.answer("Выберите пол:", reply_markup=gender_keyboard)
        await FiltersStatePendants.filter_gender_pendants.set()  # Устанавливаем состояние для ожидания пола

@dp.message_handler(state=FiltersStatePendants.filter_price_pendants)
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

        keyboard = create_filter_keyboard_pendants(await get_user_filters(user_id))
        await message.answer("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()

# Шаг 6: Обработчик для фильтра "Бренд"
@dp.callback_query_handler(state=FiltersStatePendants.filter_brand_pendants)
async def process_brand(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    async with state.proxy() as data:
        brand = callback_query.data.split("_", 2)[2]
        data['brand'] = brand

        user_id = callback_query.from_user.id

        # Сохранение фильтров пользователя в базу данных
        await save_user_filter(user_id, 'filter_brand', brand)

        # Создаем и обновляем клавиатуру с учетом выбранного бренда
        keyboard = create_filter_keyboard_pendants(await get_user_filters(user_id))
        await callback_query.message.edit_text("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()  # Завершаем состояние выбора бренда

# Шаг 6: Обработчик для фильтра "Состояние"
@dp.callback_query_handler(state=FiltersStatePendants.filter_condition_pendants)
async def process_condition(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    async with state.proxy() as data:
        data['condition'] = callback_query.data

        user_id = callback_query.from_user.id

        # Сохранение фильтров пользователя в базу данных
        await save_user_filter(user_id, 'filter_condition', data['condition'])

        # Создаем и обновляем клавиатуру с учетом выбранного состояния
        keyboard = create_filter_keyboard_pendants(await get_user_filters(user_id))
        await callback_query.message.edit_text("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()  # Завершаем состояние выбора состояния

# Шаг 7: Обработчик для фильтра "Пол"
@dp.callback_query_handler(state=FiltersStatePendants.filter_gender_pendants)
async def process_gender(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    async with state.proxy() as data:
        data['gender'] = callback_query.data

        user_id = callback_query.from_user.id

        # Сохранение фильтров пользователя в базу данных
        await save_user_filter(user_id, 'filter_gender', data['gender'])

        # Создаем и обновляем клавиатуру с учетом выбранного пола
        keyboard = create_filter_keyboard_pendants(await get_user_filters(user_id))
        await callback_query.message.edit_text("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()  # Завершаем состояние выбора пола
    
# Обработчик сброса фильтров
@dp.callback_query_handler(lambda callback_query: callback_query.data == 'reset_filters_pendants')
async def reset_filters(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    # Выполните сброс фильтров и очистите user_filters
    for key in user_filters:
        user_filters[key] = {}

    # Удалите данные о пользователе из базы данных
    await clear_user_filters(user_id)

    # Отправьте сообщение, уведомляющее пользователя о сбросе
    await bot.send_message(user_id, "Фильтры сброшены. Выберите другие новые фильтры для поиска подвесок или нажмите поиск.", reply_markup=create_filter_keyboard_pendants(user_filters))


# Обработчик для инлайн-поиска
@dp.inline_handler(lambda query: query.query == "pendants")
async def search_inline_pendants(query: InlineQuery, state: FSMContext):
    user_id = query.from_user.id  # Получаем ID пользователя из запроса
    filters = await get_user_filters(user_id)

    print(filters)
    offset = int(query.offset) if query.offset else 0
    limit = 49  # Лимит на количество часов в одной порции
    next_offset = offset + limit  # Следующая позиция начала

    # Проверяем, есть ли выбранные фильтры, и выбираем соответствующую функцию для поиска
    if not filters:
        # Если фильтры не выбраны, используем get_all_pendants без ограничения
        filtered_pendants = await get_all_pendants(limit=limit, offset=offset)
    else:
        # Иначе используем get_filtered_pendants с выбранными фильтрами
        filtered_pendants = await get_filtered_pendants(filters, limit=limit, offset=offset)

    results = []
    for pendants in filtered_pendants:
        pendants_dict = {
            'id': pendants[0],
            'manufacture': pendants[1],
            'name': pendants[2],
            'price': pendants[3],
            'for_whom': for_whom_mapping.get(pendants[4], pendants[4]),
            'conditions': condition_mapping.get(pendants[5], pendants[5]),
            'images': pendants[6],  # Поле images является шестым полем (индекс 6)
            'characteristics': pendants[7]
        }

        # Проверяем, есть ли у часов название
        if not pendants_dict['name']:
            continue  # Пропускаем результаты без названия

        # Получаем первое изображение из списка изображений
        images_list = pendants_dict['images'].split(',')  # Если изображения разделены запятыми
        first_image = images_list[0].strip() if images_list else ''  # Получаем первое изображение

        # Создаем результаты инлайн-поиска для каждого товара
        title = pendants_dict['name']
        description = f"Цена: {pendants_dict['price']}, Бренд: {pendants_dict['manufacture']}, Состояние: {pendants_dict['conditions']}, Для кого: {pendants_dict['for_whom']}"
        input_message_content = InputTextMessageContent(f"Нажмите подробнее, чтобы увидеть все изображения и всю информацию о данном товаре")
        thumb_url = first_image  # URL первого изображения товара

        results.append(
            InlineQueryResultArticle(
                id=str(pendants_dict['id']),
                title=title,
                description=description,
                input_message_content=input_message_content,
                thumb_url=thumb_url,
                reply_markup=await create_pendants_inline_keyboard(pendants_dict['id'])  # Добавляем кнопку "Подробнее"
            )
        )

    if next_offset < await get_total_pendants():  # Если есть еще часы для отображения
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

async def create_pendants_inline_keyboard(pendants_id):
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton("Подробнее", callback_data=f"pendants_{pendants_id}")
    keyboard.add(button)
    return keyboard

# Обработчик нажатия на часы
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('pendants_'))
async def pendants_callback(query: CallbackQuery, state: FSMContext):
    # Извлекаем идентификатор часов из callback_data
    pendants_id = int(query.data.split('_')[1])

    # Получаем данные о часах по идентификатору (замените на ваш метод для получения данных о часах)
    pendants_data = await get_pendants_data_by_id(pendants_id)

    # Проверяем, что данные о часах найдены
    if pendants_data:
        # Разделяем данные о часах на отдельные элементы
        pendants_name = pendants_data[2]  # Извлекаем имя часов из кортежа
        pendants_manufacture = pendants_data[1]  # Извлекаем производителя из кортежа
        pendants_price = pendants_data[3]  # Извлекаем цену из кортежа
        pendants_for_whom_text = pendants_data[4]  # Извлекаем для кого из кортежа
        pendants_for_whom = for_whom_mapping.get(pendants_for_whom_text, pendants_for_whom_text)
        pendants_conditions_text = pendants_data[5]# Извлекаем состояние из кортежа
        pendants_conditions = condition_mapping.get(pendants_conditions_text, pendants_conditions_text)
        pendants_images = pendants_data[6].split(',')  # Если изображения разделены запятыми
        pendants_characteristics = pendants_data[7]  # Извлекаем характеристики из кортежа
        
        async with state.proxy() as data:
                    data['pendants_name'] = pendants_name
                    data['pendants_manufacture'] = pendants_manufacture
                    data['pendants_price'] = pendants_price
                    data['pendants_for_whom'] = pendants_for_whom
                    data['pendants_conditions'] = pendants_conditions
                    data['pendants_images'] = pendants_images
                    data['pendants_characteristics'] = pendants_characteristics
                    
        # Отправляем данные о часах пользователю
        message_text = f"Название: {pendants_name}\nПроизводитель: {pendants_manufacture}\nЦена: {pendants_price}\nДля кого: {pendants_for_whom}\nСостояние: {pendants_conditions}\n{pendants_characteristics}"
        await bot.send_message(chat_id=query.from_user.id, text=message_text)
        
        # Создаем обычную клавиатуру с двумя кнопками: "Назад" и "Я заинтересован данными часами"
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True,  selective=True, one_time_keyboard=True)
        keyboard.add(KeyboardButton("Назад к поиску подвесок"))
        keyboard.add(KeyboardButton("Я заинтересован данной подвеской"))
        
        # Отправляем изображения часов пользователю
        for image_url in pendants_images:
            await bot.send_photo(chat_id=query.from_user.id, photo=image_url, reply_markup=keyboard)

    # Отмечаем callback_query как обработанный, чтобы избежать дополнительных нажатий
    await query.answer()

# Функция для обработки нажатия на кнопку "Я заинтересован данным товаром"
@dp.message_handler(lambda message: message.text == "Я заинтересован данной подвеской")
async def interested_in_product(message: types.Message, state: FSMContext):
    # Получаем данные о товаре из состояния FSM
    async with state.proxy() as data:
        pendants_name = data.get('pendants_name', 'N/A')
        pendants_manufacture = data.get('pendants_manufacture', 'N/A')
        pendants_price = data.get('pendants_price', 'N/A')
        pendants_for_whom = data.get('pendants_for_whom', 'N/A')
        pendants_conditions = data.get('pendants_conditions', 'N/A')
        pendants_images = data.get('pendants_images', [])
        pendants_characteristics = data.get('pendants_characteristics', 'N/A')
    
    # Получаем никнейм пользователя
    user_nickname = message.from_user.username or "Нет никнейма"

    # Формируем сообщение с данными о товаре и никнеймом пользователя
    message_text = f"Пользователь @{user_nickname} заинтересован в товаре:\n\n"
    message_text += f"Название: {pendants_name}\nПроизводитель: {pendants_manufacture}\nЦена: {pendants_price}\n"
    message_text += f"Для кого: {pendants_for_whom}\nСостояние: {pendants_conditions}\n"
    message_text += f"{pendants_characteristics}"

    # Отправляем только первое изображение в чат с определенным идентификатором (-612247085)
    if pendants_images:
        await bot.send_photo(chat_id=chat_id, photo=pendants_images[0], caption=message_text)

    # Отвечаем пользователю, что его интерес к товару передан
    await message.answer("Ваш интерес к товару передан. Мы свяжемся с вами для уточнения деталей.\n\nНажмите /menu, чтобы вернуться в главное меню.")