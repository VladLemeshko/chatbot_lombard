import logging
from aiogram.utils import executor
from create_bot import dp, bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from handlers import *
from handlers.commands import *
from handlers.filters.watches_filters import *
from handlers.filters.earrings_filters import *
from catalogs.watches_data.sqlite_watches import *
from catalogs.watches_data.parser_watches import *
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from data.users_sqlite import users_db_start
from catalogs.earrings_data.parser_earrings import *
from catalogs.earrings_data.sqlite_earrings import *
from catalogs.braclets_data.parser_braclets import *
from catalogs.braclets_data.sqlite_braclets import *
from handlers.filters.braclets_filters import *


from catalogs.rings_data.parser_rings import *
from catalogs.rings_data.sqlite_rings import *
from handlers.filters.rings_filters import *

from catalogs.pendants_data.parser_pendants import *
from catalogs.pendants_data.sqlite_pendants import *
from handlers.filters.pendants_filters import *


# настройка логирования
logging.basicConfig(level=logging.INFO)

scheduler = AsyncIOScheduler()

# Настройка времени выполнения (здесь 01:00 AM каждый день)
scheduler.add_job(schedule_task, 'cron', hour=3, minute=0, second=0, id='daily_task_1')
scheduler.add_job(schedule_task_braclets, 'cron', hour=3, minute=30, second=0, id='daily_task_2')
scheduler.add_job(schedule_task_pendants, 'cron', hour=3, minute=50, second=0, id='daily_task_3')
scheduler.add_job(schedule_task_rings, 'cron', hour=4, minute=10, second=0, id='daily_task_4')
scheduler.add_job(schedule_task_earrings, 'cron', hour=4, minute=30, second=0, id='daily_task_5')
scheduler.start()


async def on_startup(_):
    await create_settings_table()
    await users_db_start()
    print("Бот запущен, подключение к БД выполнено успешно")
    await main_parse_watches()  # Запустить парсинг
    
    await create_settings_table_earrings()
    await main_parse_earrings() # Запустить парсинг
    
    await create_settings_table_braclets()
    await main_parse_braclets()
    
    await create_settings_table_rings()
    await main_parse_rings()
    
    await create_settings_table_pendants()
    await main_parse_pendants()
    
    
async def on_shutdown(_):
    print("Бот остановлен, закрытие соединения с БД")
    conn, cursor = await create_connection()
    # Закрыть соединение с БД при выключении бота
    await close_connection(conn=conn)

# Добавляем логгирование
dp.middleware.setup(LoggingMiddleware())
    
# запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)