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
from catalogs.braclets_data.sqlite_braclets import *


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
braclets_data_dir = os.path.join(base_dir, "..", "braclets_data")
if not os.path.exists(braclets_data_dir):
    os.makedirs(braclets_data_dir)



# URL-шаблон для парсинга страниц каталога часов
url_template_braclets = "https://lombard-exclusive.ru/catalog/jevel/braslety{}"

# Асинхронная функция для парсинга данных о часах по ссылке
async def parse_braclets_details(link):
    # Отправка GET-запроса по указанной ссылке
    response = requests.get(link)
    if response.status_code == 200:
        html_code = response.text
        soup = BeautifulSoup(html_code, "html.parser")

        # Извлечение данных о часах из HTML-кода
        name_element = soup.find("h1")
        name_braclets = name_element.text.strip() if name_element else None
        print(f"Name: {name_braclets}")

        price_element_braclets = soup.find("span", class_="price")
        price_braclets = price_element_braclets.text.strip() if price_element_braclets else None
        print(f"Price: {price_braclets}")

        image_elements_braclets = soup.find_all("div", class_="product_slide")
        images_braclets = [urljoin("https://lombard-exclusive.ru", img.find("img")["src"]) for img in image_elements_braclets] if image_elements_braclets else []
        print(f"Images: {images_braclets}")

        manufacturer_element_braclets = soup.find("span", string="Производитель:")
        manufacturer_braclets = manufacturer_element_braclets.find_next("strong").text.strip() if manufacturer_element_braclets else None
        print(f"Manufacturer: {manufacturer_braclets}")

        for_whom_element_braclets = soup.find("span", string="Для кого:")
        for_whom_text_braclets = for_whom_element_braclets.find_next("strong").text.strip() if for_whom_element_braclets else None
        for_whom_braclets = for_whom_mapping.get(for_whom_text_braclets, for_whom_text_braclets)
        print(f"For Whom: {for_whom_braclets}\n*****************")

        # Извлечение характеристик и их форматирование
        characteristics = soup.find("div", class_="attributes")
        if characteristics:
            characteristics = characteristics.find_all("div", class_="item")
            characteristics_dict = {}
            for item in characteristics:
                prop = item.find("span", class_="prop").text.strip()
                val = item.find("span", class_="val").text.strip()
                characteristics_dict[prop] = val

            type_braclets = characteristics_dict.get('Тип изделия')
            insert_braclets = characteristics_dict.get('Вставка')
            material_braclets = characteristics_dict.get('Материал корпуса изделия')
            reference_braclets = characteristics_dict.get('Референс юв.')
            condition_braclets = characteristics_dict.get('Состояние')
            if condition_braclets in condition_mapping:
                condition_braclets = condition_mapping[condition_braclets]

            # Извлечение наличия
            availability_element_braclets = soup.find("span", class_="availability")
            availability_braclets = availability_element_braclets.text.strip() if availability_element_braclets else None
            print(f"Availability: {availability_braclets}")

            # Создание строки с характеристиками
            characteristics_str = ""
            if type_braclets:
                characteristics_str += f"Тип изделия: {type_braclets}\n"
            if insert_braclets:
                characteristics_str += f"Вставка: {insert_braclets}\n"
            if material_braclets:
                characteristics_str += f"Материал корпуса изделия: {material_braclets}\n"
            if reference_braclets:
                characteristics_str += f"Референс юв.: {reference_braclets}\n"
            if availability_braclets:
                characteristics_str += f"Наличие: {availability_braclets}\n"

            # Вставка данных о часах в базу данных
            await insert_braclets_details(manufacture=manufacturer_braclets, name=name_braclets, price=price_braclets, for_whom=for_whom_braclets,
                                       conditions=condition_braclets, images=",".join(images_braclets),
                                       characteristics=characteristics_str, link=link)



# Асинхронная функция для обновления общего количества часов и флага
async def update_total_braclets_and_flag():
    total_braclets = await parse_total_braclets()
    print(total_braclets)
    if total_braclets > 0:
        await update_total_braclets(total_braclets)
        await set_flag_braclets("parsed", "no")  # Сброс флага для нового парсинга
        
# Асинхронная функция для парсинга общего количества часов
async def parse_total_braclets():
    # Отправка GET-запроса на страницу каталога
    response = requests.get("https://lombard-exclusive.ru/catalog/jevel/brasletyа")
    if response.status_code == 200:
        html_code = response.text
        soup = BeautifulSoup(html_code, "html.parser")
        title_element = soup.find("h1", class_="mc-header-title")
        if title_element:
            text = title_element.text.strip()
            # Извлечение числа в скобках, например, "Швейцарские часы (340)"
            total_braclets = int(re.search(r'\((\d+)\)', text).group(1))
            await update_total_braclets(total_braclets)  # Обновление общего количества часов
            return total_braclets
    return 0

# Асинхронная функция для получения текущего количества записей в базе данных
async def get_current_count_braclets():
    conn, cursor = await create_connection_braclets()
    try:
        cursor.execute("SELECT COUNT(*) FROM braclets")
        current_count = cursor.fetchone()[0]
        return current_count
    finally:
        await close_connection_braclets(conn)



# Асинхронная функция для обновления данных о часах
async def run_update_braclets():
    conn, cursor = await create_connection_braclets()
    try:
        page_number = 1
        while True:
            page_url = url_template_braclets.format(f"?PAGEN_1={page_number}")
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
                cursor.execute("DELETE FROM braclets WHERE link = ?", (full_link,))
                conn.commit()
                await parse_braclets_details(full_link)

                await asyncio.sleep(1)  # Пауза 1 секунда между запросами

            page_number += 1

            # Проверка достижения нужного количества часов
            current_count = await get_current_count_braclets()
            total_watches = await get_total_braclets()
            if current_count >= total_watches:
                print("*********************\nДостигнуто заданное количество часов. Парсинг завершен.\n*********************")
                await set_flag_braclets("parsed", "yes")
                return  # Завершение функции run_update(), прерывающее цикл

    finally:
        await close_connection_braclets(conn)



# Асинхронная функция для сброса автоинкремента в базе данных
async def reset_autoincrement_db_braclets():
    conn, cursor = await create_connection_braclets()
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='braclets'")
        conn.commit()
    finally:
        await close_connection_braclets(conn)
        
# Асинхронная функция для выполнения парсинга часов
async def main_parse_braclets():
    # Инициализация и обновление данных перед циклом
    await create_table_braclets()
    await create_settings_table_braclets()
    await update_total_braclets_and_flag()
    await reset_autoincrement_db_braclets()

    while True:
        parsed = await get_flag_braclets("parsed")

        if parsed == "yes":
            print("Данные уже были собраны.")
            break
        else:
            print("Данные еще не были собраны. Запуск парсинга...")
            await run_update_braclets()

        await asyncio.sleep(1)



# Асинхронная функция для планирования задачи обновления данных
async def schedule_task_braclets():
    # Инициализация и обновление данных перед циклом
    await create_table_braclets()
    await create_settings_table_braclets()
    await update_total_braclets_and_flag()
    await reset_autoincrement_db_braclets()

    while True:
        await asyncio.sleep(1)
        now = datetime.now(moscow_tz)
        target_time = now.replace(hour=3, minute=30, second=0, microsecond=0)

        if now >= target_time:
            # Удаление данных из таблицы watches
            await clear_table_braclets()  # Используется новая функция для очистки таблицы

            # Обновление флага "parsed" в таблице на "no"
            await set_flag_braclets("parsed", "no")

            # Запуск задачи обновления данных
            await main_parse_braclets()

            # После завершения парсинга, проверка флага и завершение цикла, если данные уже собраны
            parsed = await get_flag_braclets("parsed")
            if parsed == "yes":
                print("Данные уже были собраны.")
                break