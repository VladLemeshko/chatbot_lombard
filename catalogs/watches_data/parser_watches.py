# Импорт необходимых библиотек и модулей
import os
import requests
from bs4 import BeautifulSoup
import asyncio
from urllib.parse import urljoin
from datetime import datetime, time
import pytz
import re

# Импорт функций для работы с базой данных SQLite
from catalogs.watches_data.sqlite_watches import *


# Словари сопоставления значений для более читаемых и удобных данных в базе
for_whom_mapping = {
    "Мужские": "gender_male",
    "Женские": "gender_female",
    "Унисекс": "gender_unisex",
}

condition_mapping = {
    "Новые": "condition_new",
    "Как новые": "condition_like_new",
    "Б/У": "condition_used",
}



# Установка временной зоны Москвы
moscow_tz = pytz.timezone('Europe/Moscow')

# Определение текущего каталога скрипта
base_dir = os.path.dirname(os.path.abspath(__file__))

# Создание каталога для хранения данных о часах, если он не существует
watches_data_dir = os.path.join(base_dir, "..", "watches_data")
if not os.path.exists(watches_data_dir):
    os.makedirs(watches_data_dir)



# URL-шаблон для парсинга страниц каталога часов
url_template = "https://lombard-exclusive.ru/catalog/shvejcarskie-chasy{}"

# Асинхронная функция для парсинга данных о часах по ссылке
async def parse_watch_details(link):
    # Отправка GET-запроса по указанной ссылке
    response = requests.get(link)
    if response.status_code == 200:
        html_code = response.text
        soup = BeautifulSoup(html_code, "html.parser")

        # Извлечение данных о часах из HTML-кода
        name_element = soup.find("h1")
        name = name_element.text.strip() if name_element else None
        print(f"Name: {name}")

        price_element = soup.find("span", class_="price")
        price = price_element.text.strip() if price_element else None
        print(f"Price: {price}")

        image_elements = soup.find_all("div", class_="product_slide")
        images = [urljoin("https://lombard-exclusive.ru", img.find("img")["src"]) for img in image_elements] if image_elements else []
        print(f"Images: {images}")

        manufacturer_element = soup.find("span", string="Производитель:")
        manufacturer = manufacturer_element.find_next("strong").text.strip() if manufacturer_element else None
        print(f"Manufacturer: {manufacturer}")

        for_whom_element = soup.find("span", string="Для кого:")
        for_whom_text = for_whom_element.find_next("strong").text.strip() if for_whom_element else None
        for_whom = for_whom_mapping.get(for_whom_text, for_whom_text)
        print(f"For Whom: {for_whom}\n*****************")

        # Извлечение характеристик и их форматирование
        characteristics = soup.find("div", class_="attributes")
        if characteristics:
            characteristics = characteristics.find_all("div", class_="item")
            characteristics_dict = {}
            for item in characteristics:
                prop = item.find("span", class_="prop").text.strip()
                val = item.find("span", class_="val").text.strip()
                characteristics_dict[prop] = val

            type = characteristics_dict.get('Тип')
            kit = characteristics_dict.get('Комплектация')
            caliber = characteristics_dict.get('Калибр')
            mechanism = characteristics_dict.get('Механизм')
            case_size = characteristics_dict.get('Размеры корпуса')
            case_material = characteristics_dict.get('Материал корпуса')
            glass = characteristics_dict.get('Стекло')
            power_reserve = characteristics_dict.get('Запас хода')
            functions = characteristics_dict.get('Функции')
            clasp = characteristics_dict.get('Застежка')
            water_resistance = characteristics_dict.get('Водонепроницаемость')
            condition = characteristics_dict.get('Состояние')
            if condition in condition_mapping:
                condition = condition_mapping[condition]
                
            # Извлечение наличия
            availability_element = soup.find("span", class_="availability")
            availability = availability_element.text.strip() if availability_element else None
            print(f"Availability: {availability}")
            
            # Создание строки с характеристиками
            characteristics_str = ""
            if type:
                characteristics_str += f"Тип: {type}\n"
            if kit:
                characteristics_str += f"Комплектация: {kit}\n"
            if caliber:
                characteristics_str += f"Калибр: {caliber}\n"
            if mechanism:
                characteristics_str += f"Механизм: {mechanism}\n"
            if case_size:
                characteristics_str += f"Размеры корпуса: {case_size}\n"
            if case_material:
                characteristics_str += f"Материал корпуса: {case_material}\n"
            if glass:
                characteristics_str += f"Стекло: {glass}\n"
            if power_reserve:
                characteristics_str += f"Запас хода: {power_reserve}\n"
            if functions:
                characteristics_str += f"Функции: {functions}\n"
            if clasp:
                characteristics_str += f"Застежка: {clasp}\n"
            if water_resistance:
                characteristics_str += f"Водонепроницаемость: {water_resistance}\n"
            if availability:
                characteristics_str += f"Наличие: {availability}\n"

            # Вставка данных о часах в базу данных
            await insert_watch_details(manufacture=manufacturer, name=name, price=price, for_whom=for_whom,
                                       conditions=condition, images=",".join(images),
                                       characteristics=characteristics_str, link=link)



# Асинхронная функция для обновления общего количества часов и флага
async def update_total_watches_and_flag():
    total_watches = await parse_total_watches()
    print(total_watches)
    if total_watches > 0:
        await update_total_watches(total_watches)
        await set_flag("parsed", "no")  # Сброс флага для нового парсинга
        
# Асинхронная функция для парсинга общего количества часов
async def parse_total_watches():
    # Отправка GET-запроса на страницу каталога
    response = requests.get("https://lombard-exclusive.ru/catalog/shvejcarskie-chasy")
    if response.status_code == 200:
        html_code = response.text
        soup = BeautifulSoup(html_code, "html.parser")
        title_element = soup.find("h1", class_="mc-header-title")
        if title_element:
            text = title_element.text.strip()
            # Извлечение числа в скобках, например, "Швейцарские часы (340)"
            total_watches = int(re.search(r'\((\d+)\)', text).group(1))
            await update_total_watches(total_watches)  # Обновление общего количества часов
            return total_watches
    return 0

# Асинхронная функция для получения текущего количества записей в базе данных
async def get_current_count():
    conn, cursor = await create_connection()
    try:
        cursor.execute("SELECT COUNT(*) FROM watches")
        current_count = cursor.fetchone()[0]
        return current_count
    finally:
        await close_connection(conn)



# Асинхронная функция для обновления данных о часах
async def run_update():
    conn, cursor = await create_connection()
    try:
        page_number = 1
        while True:
            page_url = url_template.format(f"?PAGEN_1={page_number}")
            response = requests.get(page_url)

            if response.status_code != 200:
                break

            html_code = response.text
            soup = BeautifulSoup(html_code, "html.parser")
            product_divs = soup.find_all("div", class_="mc-wrapper")

            if len(product_divs) == 0:
                break

            for product_div in product_divs:
                link = product_div.find("a", class_="mcp-title")["href"]
                full_link = urljoin("https://lombard-exclusive.ru", link)
                # Удаление существующей записи перед вставкой новой
                cursor.execute("DELETE FROM watches WHERE link = ?", (full_link,))
                conn.commit()
                await parse_watch_details(full_link)

                await asyncio.sleep(1)  # Пауза 1 секунда между запросами

            page_number += 1

            # Проверка достижения нужного количества часов
            current_count = await get_current_count()
            total_watches = await get_total_watches()
            if current_count >= total_watches:
                print("*********************\nДостигнуто заданное количество часов. Парсинг завершен.\n*********************")
                await set_flag("parsed", "yes")
                return  # Завершение функции run_update(), прерывающее цикл

    finally:
        await close_connection(conn)



# Асинхронная функция для сброса автоинкремента в базе данных
async def reset_autoincrement_db():
    conn, cursor = await create_connection()
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='watches'")
        conn.commit()
    finally:
        await close_connection(conn)
        
# Асинхронная функция для выполнения парсинга часов
async def main_parse_watches():
    # Инициализация и обновление данных перед циклом
    await create_table()
    await create_settings_table()
    await update_total_watches_and_flag()
    await reset_autoincrement_db()

    while True:
        parsed = await get_flag("parsed")

        if parsed == "yes":
            print("Данные уже были собраны.")
            break
        else:
            print("Данные еще не были собраны. Запуск парсинга...")
            await run_update()

        await asyncio.sleep(1)



# Асинхронная функция для планирования задачи обновления данных
async def schedule_task():
    # Инициализация и обновление данных перед циклом
    await create_table()
    await create_settings_table()
    await update_total_watches_and_flag()
    await reset_autoincrement_db()

    while True:
        await asyncio.sleep(1)
        now = datetime.now(moscow_tz)
        target_time = now.replace(hour=3, minute=0, second=0, microsecond=0)

        if now >= target_time:
            # Удаление данных из таблицы watches
            await clear_table()  # Используется новая функция для очистки таблицы

            # Обновление флага "parsed" в таблице на "no"
            await set_flag("parsed", "no")

            # Запуск задачи обновления данных
            await main_parse_watches()

            # После завершения парсинга, проверка флага и завершение цикла, если данные уже собраны
            parsed = await get_flag("parsed")
            if parsed == "yes":
                print("Данные уже были собраны.")
                break