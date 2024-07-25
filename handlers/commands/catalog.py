# Импорт необходимых модулей и функций
from aiogram import types
from create_bot import dp, bot  # Подставьте правильный импорт для вашего бота
from aiogram.dispatcher import FSMContext

from keyboards.watches_kb import create_filter_keyboard
from keyboards.earrings_kb import create_filter_keyboard_earrings
from keyboards.categories_kb import get_categories_kb_class
from data.users_sqlite import get_user_filters
from data.users_sqlite import clear_user_filters
from keyboards.braclets_kb import create_filter_keyboard_braclets

from keyboards.rings_kb import create_filter_keyboard_rings

from keyboards.pendants_kb import create_filter_keyboard_pendants

    
# Обработчик для команды "Каталог"
@dp.message_handler(lambda message: message.text == "Каталог")
async def catalog(message: types.Message):
    await message.delete()
    await message.answer("Выберите категорию товаров:", reply_markup=get_categories_kb_class())

@dp.message_handler(lambda message: message.text == "Швейцарские часы" or message.text == "Назад к поиску часов", state="*")
async def swiss_watches(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await state.finish()
    await message.delete()
    await bot.send_message(chat_id=message.from_user.id,
                            text="Выберите фильтр для товаров или нажмите поиск, чтобы посмотреть все часы:\n\n",
                            reply_markup=create_filter_keyboard(await get_user_filters(user_id)))
    
@dp.message_handler(lambda message: message.text == "Серьги" or message.text == "Назад к поиску серьг", state="*")
async def earrings(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await state.finish()
    await message.delete()
    await bot.send_message(chat_id=message.from_user.id,
                            text="Выберите фильтр для товаров или нажмите поиск, чтобы посмотреть все серьги:\n\n",
                            reply_markup=create_filter_keyboard_earrings(await get_user_filters(user_id)))
    
@dp.message_handler(lambda message: message.text == "Браслеты" or message.text == "Назад к поиску браслетов", state="*")
async def braclets(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await state.finish()
    await message.delete()
    await bot.send_message(chat_id=message.from_user.id,
                            text="Выберите фильтр для товаров или нажмите поиск, чтобы посмотреть все браслеты:\n\n",
                            reply_markup=create_filter_keyboard_braclets(await get_user_filters(user_id)))
    
@dp.message_handler(lambda message: message.text == "Кольца" or message.text == "Назад к поиску колец", state="*")
async def rings(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await state.finish()
    await message.delete()
    await bot.send_message(chat_id=message.from_user.id,
                            text="Выберите фильтр для товаров или нажмите поиск, чтобы посмотреть все кольца:\n\n",
                            reply_markup=create_filter_keyboard_rings(await get_user_filters(user_id)))
    
@dp.message_handler(lambda message: message.text == "Подвески" or message.text == "Назад к поиску подвесок", state="*")
async def pendants(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await state.finish()
    await message.delete()
    await bot.send_message(chat_id=message.from_user.id,
                            text="Выберите фильтр для товаров или нажмите поиск, чтобы посмотреть все подвески:\n\n",
                            reply_markup=create_filter_keyboard_pendants(await get_user_filters(user_id)))