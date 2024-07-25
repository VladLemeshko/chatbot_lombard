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
from catalogs.pendants_data.sqlite_pendants import *


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
pendants_data_dir = os.path.join(base_dir, "..", "pendants_data")
if not os.path.exists(pendants_data_dir):
    os.makedirs(pendants_data_dir)



# URL-шаблон для парсинга страниц каталога часов
url_template_pendants = "https://lombard-exclusive.ru/catalog/jevel/podveski{}"

# Асинхронная функция для парсинга данных о часах по ссылке
async def parse_pendants_details(link):
    # Отправка GET-запроса по указанной ссылке
    response = requests.get(link)
    if response.status_code == 200:
        html_code = response.text
        soup = BeautifulSoup(html_code, "html.parser")

        # Извлечение данных о часах из HTML-кода
        name_element = soup.find("h1")
        name_pendants = name_element.text.strip() if name_element else None
        print(f"Name: {name_pendants}")

        price_element_pendants = soup.find("span", class_="price")
        price_pendants = price_element_pendants.text.strip() if price_element_pendants else None
        print(f"Price: {price_pendants}")

        image_elements_pendants = soup.find_all("div", class_="product_slide")
        images_pendants = [urljoin("https://lombard-exclusive.ru", img.find("img")["src"]) for img in image_elements_pendants] if image_elements_pendants else []
        print(f"Images: {images_pendants}")

        manufacturer_element_pendants = soup.find("span", string="Производитель:")
        manufacturer_pendants = manufacturer_element_pendants.find_next("strong").text.strip() if manufacturer_element_pendants else None
        print(f"Manufacturer: {manufacturer_pendants}")

        for_whom_element_pendants = soup.find("span", string="Для кого:")
        for_whom_text_pendants = for_whom_element_pendants.find_next("strong").text.strip() if for_whom_element_pendants else None
        for_whom_pendants = for_whom_mapping.get(for_whom_text_pendants, for_whom_text_pendants)
        print(f"For Whom: {for_whom_pendants}\n*****************")

        # Извлечение характеристик и их форматирование
        characteristics = soup.find("div", class_="attributes")
        if characteristics:
            characteristics = characteristics.find_all("div", class_="item")
            characteristics_dict = {}
            for item in characteristics:
                prop = item.find("span", class_="prop").text.strip()
                val = item.find("span", class_="val").text.strip()
                characteristics_dict[prop] = val

            type_pendants = characteristics_dict.get('Тип изделия')
            size_pendants = characteristics_dict.get('Размер')
            insert_pendants = characteristics_dict.get('Вставка')
            material_pendants = characteristics_dict.get('Материал корпуса изделия')
            reference_pendants = characteristics_dict.get('Референс юв.')
            condition_pendants = characteristics_dict.get('Состояние')
            if condition_pendants in condition_mapping:
                condition_pendants = condition_mapping[condition_pendants]

            # Извлечение наличия
            availability_element_pendants = soup.find("span", class_="availability")
            availability_pendants = availability_element_pendants.text.strip() if availability_element_pendants else None
            print(f"Availability: {availability_pendants}")
            
            # Создание строки с характеристиками
            characteristics_str = ""
            if type_pendants:
                characteristics_str += f"Тип изделия: {type_pendants}\n"
            if size_pendants:
                characteristics_str += f"Размер: {size_pendants}\n"
            if insert_pendants:
                characteristics_str += f"Вставка: {insert_pendants}\n"
            if material_pendants:
                characteristics_str += f"Материал корпуса изделия: {material_pendants}\n"
            if reference_pendants:
                characteristics_str += f"Референс юв.: {reference_pendants}\n"
            if availability_pendants:
                characteristics_str += f"Наличие: {availability_pendants}\n"

            # Вставка данных о часах в базу данных
            await insert_pendants_details(manufacture=manufacturer_pendants, name=name_pendants, price=price_pendants, for_whom=for_whom_pendants,
                                       conditions=condition_pendants, images=",".join(images_pendants),
                                       characteristics=characteristics_str, link=link)



# Асинхронная функция для обновления общего количества часов и флага
async def update_total_pendants_and_flag():
    total_pendants = await parse_total_pendants()
    print(total_pendants)
    if total_pendants > 0:
        await update_total_pendants(total_pendants)
        await set_flag_pendants("parsed", "no")  # Сброс флага для нового парсинга
        
# Асинхронная функция для парсинга общего количества часов
async def parse_total_pendants():
    # Отправка GET-запроса на страницу каталога
    response = requests.get("https://lombard-exclusive.ru/catalog/jevel/podveski")
    if response.status_code == 200:
        html_code = response.text
        soup = BeautifulSoup(html_code, "html.parser")
        title_element = soup.find("h1", class_="mc-header-title")
        if title_element:
            text = title_element.text.strip()
            # Извлечение числа в скобках, например, "Швейцарские часы (340)"
            total_pendants = int(re.search(r'\((\d+)\)', text).group(1))
            await update_total_pendants(total_pendants)  # Обновление общего количества часов
            return total_pendants
    return 0

# Асинхронная функция для получения текущего количества записей в базе данных
async def get_current_count_pendants():
    conn, cursor = await create_connection_pendants()
    try:
        cursor.execute("SELECT COUNT(*) FROM pendants")
        current_count = cursor.fetchone()[0]
        return current_count
    finally:
        await close_connection_pendants(conn)



# Асинхронная функция для обновления данных о часах
async def run_update_pendants():
    conn, cursor = await create_connection_pendants()
    try:
        page_number = 1
        while True:
            page_url = url_template_pendants.format(f"?PAGEN_1={page_number}")
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
                cursor.execute("DELETE FROM pendants WHERE link = ?", (full_link,))
                conn.commit()
                await parse_pendants_details(full_link)

                await asyncio.sleep(1)  # Пауза 1 секунда между запросами

            page_number += 1

            # Проверка достижения нужного количества часов
            current_count = await get_current_count_pendants()
            total_watches = await get_total_pendants()
            if current_count >= total_watches:
                print("*********************\nДостигнуто заданное количество часов. Парсинг завершен.\n*********************")
                await set_flag_pendants("parsed", "yes")
                return  # Завершение функции run_update(), прерывающее цикл

    finally:
        await close_connection_pendants(conn)



# Асинхронная функция для сброса автоинкремента в базе данных
async def reset_autoincrement_db_pendants():
    conn, cursor = await create_connection_pendants()
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='pendants'")
        conn.commit()
    finally:
        await close_connection_pendants(conn)
        
# Асинхронная функция для выполнения парсинга часов
async def main_parse_pendants():
    # Инициализация и обновление данных перед циклом
    await create_table_pendants()
    await create_settings_table_pendants()
    await update_total_pendants_and_flag()
    await reset_autoincrement_db_pendants()

    while True:
        parsed = await get_flag_pendants("parsed")

        if parsed == "yes":
            print("Данные уже были собраны.")
            break
        else:
            print("Данные еще не были собраны. Запуск парсинга...")
            await run_update_pendants()

        await asyncio.sleep(1)



# Асинхронная функция для планирования задачи обновления данных
async def schedule_task_pendants():
    # Инициализация и обновление данных перед циклом
    await create_table_pendants()
    await create_settings_table_pendants()
    await update_total_pendants_and_flag()
    await reset_autoincrement_db_pendants()

    while True:
        await asyncio.sleep(1)
        now = datetime.now(moscow_tz)
        target_time = now.replace(hour=3, minute=50, second=0, microsecond=0)

        if now >= target_time:
            # Удаление данных из таблицы watches
            await clear_table_pendants()  # Используется новая функция для очистки таблицы

            # Обновление флага "parsed" в таблице на "no"
            await set_flag_pendants("parsed", "no")

            # Запуск задачи обновления данных
            await main_parse_pendants()

            # После завершения парсинга, проверка флага и завершение цикла, если данные уже собраны
            parsed = await get_flag_pendants("parsed")
            if parsed == "yes":
                print("Данные уже были собраны.")
                break