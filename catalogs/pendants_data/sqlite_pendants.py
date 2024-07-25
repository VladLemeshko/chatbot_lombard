# Импортируем необходимые библиотеки
import sqlite3  # Для работы с базой данных SQLite
import os  # Для работы с файловой системой



# Определяем путь к текущему каталогу скрипта
base_dir = os.path.dirname(os.path.abspath(__file__))

# Определяем каталог для хранения данных о часах, относительно текущего каталога
pendants_data_dir = os.path.join(base_dir, "..", "pendants_data")

# Создаем каталог watches_data, если его не существует
if not os.path.exists(pendants_data_dir):
    os.makedirs(pendants_data_dir)

# Определяем путь к файлу базы данных SQLite
db_path_pendants = os.path.join(pendants_data_dir, "pendants.db")

# Асинхронная функция для создания соединения с базой данных и получения курсора
async def create_connection_pendants():
    conn = sqlite3.connect(db_path_pendants)
    cursor = conn.cursor()
    return conn, cursor

# Асинхронная функция для закрытия соединения с базой данных
async def close_connection_pendants(conn):
    conn.commit()
    conn.close()



# Асинхронная функция для создания таблицы настроек
async def create_settings_table_pendants():
    conn, cursor = await create_connection_pendants()
    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            value TEXT
        )
        """
        cursor.execute(create_table_query)
    finally:
        await close_connection_pendants(conn)
        
# Асинхронная функция для обновления настройки
async def update_setting_pendants(name, value):
    conn, cursor = await create_connection_pendants()
    try:
        cursor.execute("INSERT OR REPLACE INTO settings (name, value) VALUES (?, ?)", (name, value))
        conn.commit()
    finally:
        await close_connection_pendants(conn)

# Асинхронная функция для получения значения настройки
async def get_setting_pendants(name):
    conn, cursor = await create_connection_pendants()
    try:
        cursor.execute("SELECT value FROM settings WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return None
    finally:
        await close_connection_pendants(conn)

async def set_flag_pendants(flag_name, value):
    await update_setting_pendants(flag_name, value)

async def get_flag_pendants(flag_name):
    return await get_setting_pendants(flag_name)

async def get_total_pendants():
    total_pendants = await get_setting_pendants("total_pendants")
    if total_pendants is None:
        return 0
    else:
        return int(total_pendants)
    
async def update_total_pendants(total_pendants):
    await update_setting_pendants("total_pendants", str(total_pendants))
    


# Асинхронная функция для создания таблицы "pendants"
async def create_table_pendants():
    conn, cursor = await create_connection_pendants()
    try:
        create_table_query = """
            CREATE TABLE IF NOT EXISTS pendants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manufacture TEXT,
                name TEXT,
                price TEXT,
                for_whom TEXT,
                conditions TEXT,
                images TEXT,
                characteristics TEXT,
                link TEXT
            )
            """
        cursor.execute(create_table_query)
    finally:
        await close_connection_pendants(conn)

# Асинхронная функция для очистки таблицы "watches"
async def clear_table_pendants():
    conn, cursor = await create_connection_pendants()
    try:
        cursor.execute("DELETE FROM pendants")
        conn.commit()
    finally:
        await close_connection_pendants(conn)


           
# Асинхронная функция для вставки данных о часах
async def insert_pendants_details(**kwargs):
    conn, cursor = await create_connection_pendants()
    try:
        insert_query = """
        INSERT OR REPLACE INTO pendants (manufacture, name, price, for_whom, conditions, images, characteristics, link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            kwargs.get('manufacture'), kwargs.get('name'), kwargs.get('price'), kwargs.get('for_whom'),
            kwargs.get('conditions'), kwargs.get('images'), kwargs.get('characteristics'), kwargs.get('link')
        )
        cursor.execute(insert_query, values)
        conn.commit()
    finally:
        await close_connection_pendants(conn)




# Асинхронная функция для получения диапазона цен
async def get_price_range_pendants():
    conn, cursor = await create_connection_pendants()
    try:
        cursor.execute("SELECT MIN(CAST(REPLACE(REPLACE(price, ',', ''), '$', '') AS INTEGER)), MAX(CAST(REPLACE(REPLACE(price, ',', ''), '$', '') AS INTEGER)) FROM pendants")
        min_price, max_price = cursor.fetchone()
        return min_price, max_price
    finally:
        await close_connection_pendants(conn) 
        
# Асинхронная функция для получения списка уникальных брендов
async def get_unique_brands_pendants():
    conn, cursor = await create_connection_pendants()
    try:
        cursor.execute("SELECT DISTINCT manufacture FROM pendants WHERE manufacture IS NOT NULL")
        
        unique_brands = [row[0] for row in cursor.fetchall()]
        print(unique_brands)
        return unique_brands
    finally:
        await close_connection_pendants(conn) 
        
        
                 
# Асинхронная функция для получения всех часов с возможностью установки лимита и смещения
async def get_all_pendants(limit=None, offset=None):
    conn, cursor = await create_connection_pendants()
    try:
        query = "SELECT id, manufacture, name, price, for_whom, conditions, images, characteristics FROM pendants"
        if limit is not None:
            query += " LIMIT ?"
        if offset is not None:
            query += " OFFSET ?"
        cursor.execute(query, (limit, offset))
        pendants = cursor.fetchall()
        return pendants
    finally:
        await close_connection_pendants(conn)

# Асинхронная функция для фильтрации часов по различным критериям
async def get_filtered_pendants(filters, limit=None, offset=None):
    conn, cursor = await create_connection_pendants()
    try:
        params = []
        where_conditions = []
        
        for key, value in filters.items():
            if key == 'filter_price':
                price_filter = value
                if price_filter['min_price'] is not None and price_filter['max_price'] is not None:
                    where_conditions.append("CAST(REPLACE(REPLACE(price, ',', ''), '$', '') AS INTEGER) BETWEEN ? AND ?")
                    params.extend([price_filter['min_price'], price_filter['max_price']])
            elif key == 'filter_brand':
                brand_filter = value
                if brand_filter['brand'] is not None:
                    where_conditions.append("manufacture = ?")
                    params.append(brand_filter['brand'])
            elif key == 'filter_condition':
                condition_filter = value
                if condition_filter['condition'] is not None:
                    where_conditions.append("conditions = ?")
                    params.append(condition_filter['condition'])
            elif key == 'filter_gender':
                gender_filter = value
                if gender_filter['gender'] is not None:
                    where_conditions.append("for_whom = ?")
                    params.append(gender_filter['gender'])

        query = f"""
            SELECT id, manufacture, name, price, for_whom, conditions, images, characteristics
            FROM pendants
            WHERE 1=1
        """

        if where_conditions:
            query += " AND " + " AND ".join(where_conditions)

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)

        cursor.execute(query, params)
        pendants = cursor.fetchall()
        return pendants
    finally:
        await close_connection_pendants(conn)




# Асинхронная функция для получения данных о часе по его идентификатору
async def get_pendants_data_by_id(watch_id):
    conn, cursor = await create_connection_pendants()
    try:
        cursor.execute("SELECT id, manufacture, name, price, for_whom, conditions, images, characteristics FROM pendants WHERE id = ?", (watch_id,))
        pendants_data = cursor.fetchone()
        return pendants_data
    finally:
        await close_connection_pendants(conn)