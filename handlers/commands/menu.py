# Импорт необходимых модулей и библиотек
from create_bot import dp, bot 
from aiogram import types  
from keyboards.menu_kb import get_menu_kb_class  
from aiogram.dispatcher import FSMContext



# Обработчик команды "/menu"
@dp.message_handler(commands=['menu'], state="*")
async def menu_command(message: types.Message, state: FSMContext):
    menu_text = "Вы находитесь в главном меню. Пожалуйста, выберите нужное действие."
    await state.finish()
    await message.delete()  # Удаление исходного сообщения, содержащего команду "/menu"

    # Отправка сообщения с текстом меню и клавиатурой, полученной из функции 'get_menu_kb_class'
    await bot.send_message(chat_id=message.from_user.id,
                            text=menu_text,
                            reply_markup=get_menu_kb_class())