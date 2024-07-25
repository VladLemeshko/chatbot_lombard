from aiogram import types
from aiogram.types import Message, InputTextMessageContent, InlineQuery, InlineQueryResultArticle, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery
from create_bot import dp, bot  # Подставьте правильный импорт для вашего бота

# Импорт функций для работы с данными о часах
from catalogs.braclets_data.sqlite_braclets import get_all_braclets, get_filtered_braclets, get_price_range_braclets, get_total_braclets, get_braclets_data_by_id, get_unique_brands_braclets
from keyboards.coditiion_kb import condition_keyboard
from keyboards.gender_kb import gender_keyboard
from keyboards.braclets_kb import create_filter_keyboard_braclets
from data.users_sqlite import save_user_filter, get_user_filters, clear_user_filters
from states.FilterStatesBraclets import FiltersStateBraclets
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
@dp.callback_query_handler(lambda query: query.data in ["filter_price_braclets", "filter_brand_braclets", "filter_condition_braclets", "filter_gender_braclets"], state="*")
async def apply_filter(query: CallbackQuery, state: FSMContext):
    await query.answer()
    filter_name = query.data.replace("filter_", "")  # Извлекаем имя фильтра из данных кнопки

    # Завершаем общее состояние выбора фильтра
    await FiltersStateBraclets.filter_selected_braclets.set()

    # Здесь мы сохраняем выбранный фильтр в состоянии (FSM)
    async with state.proxy() as data:
        data['filter'] = filter_name
    print(data)
    # Здесь вы можете добавить логику запроса необходимых данных у пользователя
    if filter_name == "price_braclets":
        min_price, max_price = await get_price_range_braclets()  # Получаем минимальную и максимальную цену из БД
        await query.message.answer(f"Введите диапазон цен в долларах (минимальная: {min_price}$ и максимальная: {max_price}$, например, 3000-15000):")
        await FiltersStateBraclets.filter_price_braclets.set()  # Устанавливаем состояние для ожидания ценового диапазона
        
    if filter_name == "brand_braclets":
        # Получаем уникальные бренды из базы данных
        unique_brands = await get_unique_brands_braclets()
        
        # Создаем кнопки для каждого бренда
        brand_buttons = [InlineKeyboardButton(text=brand, callback_data=f"select_brand_{brand}") for brand in unique_brands]
        
        rows = [brand_buttons[i:i + 2] for i in range(0, len(brand_buttons), 2)]
        
        # Добавляем кнопки в клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

        await query.message.answer("Выберите бренд:", reply_markup=keyboard)
        await FiltersStateBraclets.filter_brand_braclets.set()

                
    elif filter_name == "condition_braclets":
        await query.message.answer("Выберите состояние:", reply_markup=condition_keyboard)
        await FiltersStateBraclets.filter_condition_braclets.set()  # Устанавливаем состояние для ожидания состояния
    elif filter_name == "gender_braclets":
        await query.message.answer("Выберите пол:", reply_markup=gender_keyboard)
        await FiltersStateBraclets.filter_gender_braclets.set()  # Устанавливаем состояние для ожидания пола

@dp.message_handler(state=FiltersStateBraclets.filter_price_braclets)
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

        keyboard = create_filter_keyboard_braclets(await get_user_filters(user_id))
        await message.answer("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()

# Шаг 6: Обработчик для фильтра "Бренд"
@dp.callback_query_handler(state=FiltersStateBraclets.filter_brand_braclets)
async def process_brand(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    async with state.proxy() as data:
        brand = callback_query.data.split("_", 2)[2]
        data['brand'] = brand

        user_id = callback_query.from_user.id

        # Сохранение фильтров пользователя в базу данных
        await save_user_filter(user_id, 'filter_brand', brand)

        # Создаем и обновляем клавиатуру с учетом выбранного бренда
        keyboard = create_filter_keyboard_braclets(await get_user_filters(user_id))
        await callback_query.message.edit_text("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()  # Завершаем состояние выбора бренда

# Шаг 6: Обработчик для фильтра "Состояние"
@dp.callback_query_handler(state=FiltersStateBraclets.filter_condition_braclets)
async def process_condition(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    async with state.proxy() as data:
        data['condition'] = callback_query.data

        user_id = callback_query.from_user.id

        # Сохранение фильтров пользователя в базу данных
        await save_user_filter(user_id, 'filter_condition', data['condition'])

        # Создаем и обновляем клавиатуру с учетом выбранного состояния
        keyboard = create_filter_keyboard_braclets(await get_user_filters(user_id))
        await callback_query.message.edit_text("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()  # Завершаем состояние выбора состояния

# Шаг 7: Обработчик для фильтра "Пол"
@dp.callback_query_handler(state=FiltersStateBraclets.filter_gender_braclets)
async def process_gender(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()

    async with state.proxy() as data:
        data['gender'] = callback_query.data

        user_id = callback_query.from_user.id

        # Сохранение фильтров пользователя в базу данных
        await save_user_filter(user_id, 'filter_gender', data['gender'])

        # Создаем и обновляем клавиатуру с учетом выбранного пола
        keyboard = create_filter_keyboard_braclets(await get_user_filters(user_id))
        await callback_query.message.edit_text("Выберите другой фильтр или нажмите поиск:", reply_markup=keyboard)

        await state.finish()  # Завершаем состояние выбора пола
    
# Обработчик сброса фильтров
@dp.callback_query_handler(lambda callback_query: callback_query.data == 'reset_filters_braclets')
async def reset_filters(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    # Выполните сброс фильтров и очистите user_filters
    for key in user_filters:
        user_filters[key] = {}

    # Удалите данные о пользователе из базы данных
    await clear_user_filters(user_id)

    # Отправьте сообщение, уведомляющее пользователя о сбросе
    await bot.send_message(user_id, "Фильтры сброшены. Выберите другие новые фильтры для поиска браслетов или нажмите поиск.", reply_markup=create_filter_keyboard_braclets(user_filters))


# Обработчик для инлайн-поиска
@dp.inline_handler(lambda query: query.query == "braclets")
async def search_inline_braclets(query: InlineQuery, state: FSMContext):
    user_id = query.from_user.id  # Получаем ID пользователя из запроса
    filters = await get_user_filters(user_id)

    print(filters)
    offset = int(query.offset) if query.offset else 0
    limit = 49  # Лимит на количество часов в одной порции
    next_offset = offset + limit  # Следующая позиция начала

    # Проверяем, есть ли выбранные фильтры, и выбираем соответствующую функцию для поиска
    if not filters:
        # Если фильтры не выбраны, используем get_all_braclets без ограничения
        filtered_braclets = await get_all_braclets(limit=limit, offset=offset)
    else:
        # Иначе используем get_filtered_braclets с выбранными фильтрами
        filtered_braclets = await get_filtered_braclets(filters, limit=limit, offset=offset)

    results = []
    for braclets in filtered_braclets:
        braclets_dict = {
            'id': braclets[0],
            'manufacture': braclets[1],
            'name': braclets[2],
            'price': braclets[3],
            'for_whom': for_whom_mapping.get(braclets[4], braclets[4]),
            'conditions': condition_mapping.get(braclets[5], braclets[5]),
            'images': braclets[6],  # Поле images является шестым полем (индекс 6)
            'characteristics': braclets[7]
        }

        # Проверяем, есть ли у часов название
        if not braclets_dict['name']:
            continue  # Пропускаем результаты без названия

        # Получаем первое изображение из списка изображений
        images_list = braclets_dict['images'].split(',')  # Если изображения разделены запятыми
        first_image = images_list[0].strip() if images_list else ''  # Получаем первое изображение

        # Создаем результаты инлайн-поиска для каждого товара
        title = braclets_dict['name']
        description = f"Цена: {braclets_dict['price']}, Бренд: {braclets_dict['manufacture']}, Состояние: {braclets_dict['conditions']}, Для кого: {braclets_dict['for_whom']}"
        input_message_content = InputTextMessageContent(f"Нажмите подробнее, чтобы увидеть все изображения и всю информацию о данном товаре")
        thumb_url = first_image  # URL первого изображения товара

        results.append(
            InlineQueryResultArticle(
                id=str(braclets_dict['id']),
                title=title,
                description=description,
                input_message_content=input_message_content,
                thumb_url=thumb_url,
                reply_markup=await create_braclets_inline_keyboard(braclets_dict['id'])  # Добавляем кнопку "Подробнее"
            )
        )

    if next_offset < await get_total_braclets():  # Если есть еще часы для отображения
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

async def create_braclets_inline_keyboard(braclets_id):
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton("Подробнее", callback_data=f"braclets_{braclets_id}")
    keyboard.add(button)
    return keyboard

# Обработчик нажатия на часы
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('braclets_'))
async def braclets_callback(query: CallbackQuery, state: FSMContext):
    # Извлекаем идентификатор часов из callback_data
    braclets_id = int(query.data.split('_')[1])

    # Получаем данные о часах по идентификатору (замените на ваш метод для получения данных о часах)
    braclets_data = await get_braclets_data_by_id(braclets_id)

    # Проверяем, что данные о часах найдены
    if braclets_data:
        # Разделяем данные о часах на отдельные элементы
        braclets_name = braclets_data[2]  # Извлекаем имя часов из кортежа
        braclets_manufacture = braclets_data[1]  # Извлекаем производителя из кортежа
        braclets_price = braclets_data[3]  # Извлекаем цену из кортежа
        braclets_for_whom_text = braclets_data[4]  # Извлекаем для кого из кортежа
        braclets_for_whom = for_whom_mapping.get(braclets_for_whom_text, braclets_for_whom_text)
        braclets_conditions_text = braclets_data[5]# Извлекаем состояние из кортежа
        braclets_conditions = condition_mapping.get(braclets_conditions_text, braclets_conditions_text)
        braclets_images = braclets_data[6].split(',')  # Если изображения разделены запятыми
        braclets_characteristics = braclets_data[7]  # Извлекаем характеристики из кортежа
        
        async with state.proxy() as data:
                    data['braclets_name'] = braclets_name
                    data['braclets_manufacture'] = braclets_manufacture
                    data['braclets_price'] = braclets_price
                    data['braclets_for_whom'] = braclets_for_whom
                    data['braclets_conditions'] = braclets_conditions
                    data['braclets_images'] = braclets_images
                    data['braclets_characteristics'] = braclets_characteristics
                    
        # Отправляем данные о часах пользователю
        message_text = f"Название: {braclets_name}\nПроизводитель: {braclets_manufacture}\nЦена: {braclets_price}\nДля кого: {braclets_for_whom}\nСостояние: {braclets_conditions}\n{braclets_characteristics}"
        await bot.send_message(chat_id=query.from_user.id, text=message_text)
        
        # Создаем обычную клавиатуру с двумя кнопками: "Назад" и "Я заинтересован данными часами"
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True,  selective=True, one_time_keyboard=True)
        keyboard.add(KeyboardButton("Назад к поиску браслетов"))
        keyboard.add(KeyboardButton("Я заинтересован данным браслетом"))
        
        # Отправляем изображения часов пользователю
        for image_url in braclets_images:
            await bot.send_photo(chat_id=query.from_user.id, photo=image_url, reply_markup=keyboard)

    # Отмечаем callback_query как обработанный, чтобы избежать дополнительных нажатий
    await query.answer()

# Функция для обработки нажатия на кнопку "Я заинтересован данным товаром"
@dp.message_handler(lambda message: message.text == "Я заинтересован данным браслетом")
async def interested_in_product(message: types.Message, state: FSMContext):
    # Получаем данные о товаре из состояния FSM
    async with state.proxy() as data:
        braclets_name = data.get('braclets_name', 'N/A')
        braclets_manufacture = data.get('braclets_manufacture', 'N/A')
        braclets_price = data.get('braclets_price', 'N/A')
        braclets_for_whom = data.get('braclets_for_whom', 'N/A')
        braclets_conditions = data.get('braclets_conditions', 'N/A')
        braclets_images = data.get('braclets_images', [])
        braclets_characteristics = data.get('braclets_characteristics', 'N/A')
    
    # Получаем никнейм пользователя
    user_nickname = message.from_user.username or "Нет никнейма"

    # Формируем сообщение с данными о товаре и никнеймом пользователя
    message_text = f"Пользователь @{user_nickname} заинтересован в товаре:\n\n"
    message_text += f"Название: {braclets_name}\nПроизводитель: {braclets_manufacture}\nЦена: {braclets_price}\n"
    message_text += f"Для кого: {braclets_for_whom}\nСостояние: {braclets_conditions}\n"
    message_text += f"{braclets_characteristics}"

    # Отправляем только первое изображение в чат с определенным идентификатором (-612247085)
    if braclets_images:
        await bot.send_photo(chat_id=chat_id, photo=braclets_images[0], caption=message_text)

    # Отвечаем пользователю, что его интерес к товару передан
    await message.answer("Ваш интерес к товару передан. Мы свяжемся с вами для уточнения деталей.\n\nНажмите /menu, чтобы вернуться в главное меню.")