# Импортируем необходимые библиотеки
import sqlite3  # Для работы с базой данных SQLite
import os  # Для работы с файловой системой



# Определяем путь к текущему каталогу скрипта
base_dir = os.path.dirname(os.path.abspath(__file__))

# Определяем каталог для хранения данных о часах, относительно текущего каталога
rings_data_dir = os.path.join(base_dir, "..", "rings_data")

# Создаем каталог watches_data, если его не существует
if not os.path.exists(rings_data_dir):
    os.makedirs(rings_data_dir)

# Определяем путь к файлу базы данных SQLite
db_path_rings = os.path.join(rings_data_dir, "rings.db")

# Асинхронная функция для создания соединения с базой данных и получения курсора
async def create_connection_rings():
    conn = sqlite3.connect(db_path_rings)
    cursor = conn.cursor()
    return conn, cursor

# Асинхронная функция для закрытия соединения с базой данных
async def close_connection_rings(conn):
    conn.commit()
    conn.close()



# Асинхронная функция для создания таблицы настроек
async def create_settings_table_rings():
    conn, cursor = await create_connection_rings()
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
        await close_connection_rings(conn)
        
# Асинхронная функция для обновления настройки
async def update_setting_rings(name, value):
    conn, cursor = await create_connection_rings()
    try:
        cursor.execute("INSERT OR REPLACE INTO settings (name, value) VALUES (?, ?)", (name, value))
        conn.commit()
    finally:
        await close_connection_rings(conn)

# Асинхронная функция для получения значения настройки
async def get_setting_rings(name):
    conn, cursor = await create_connection_rings()
    try:
        cursor.execute("SELECT value FROM settings WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return None
    finally:
        await close_connection_rings(conn)

async def set_flag_rings(flag_name, value):
    await update_setting_rings(flag_name, value)

async def get_flag_rings(flag_name):
    return await get_setting_rings(flag_name)

async def get_total_rings():
    total_rings = await get_setting_rings("total_rings")
    if total_rings is None:
        return 0
    else:
        return int(total_rings)
    
async def update_total_rings(total_rings):
    await update_setting_rings("total_rings", str(total_rings))
    


# Асинхронная функция для создания таблицы "rings"
async def create_table_rings():
    conn, cursor = await create_connection_rings()
    try:
        create_table_query = """
            CREATE TABLE IF NOT EXISTS rings (
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
        await close_connection_rings(conn)

# Асинхронная функция для очистки таблицы "watches"
async def clear_table_rings():
    conn, cursor = await create_connection_rings()
    try:
        cursor.execute("DELETE FROM rings")
        conn.commit()
    finally:
        await close_connection_rings(conn)


           
# Асинхронная функция для вставки данных о часах
async def insert_rings_details(**kwargs):
    conn, cursor = await create_connection_rings()
    try:
        insert_query = """
        INSERT OR REPLACE INTO rings (manufacture, name, price, for_whom, conditions, images, characteristics, link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            kwargs.get('manufacture'), kwargs.get('name'), kwargs.get('price'), kwargs.get('for_whom'),
            kwargs.get('conditions'), kwargs.get('images'), kwargs.get('characteristics'), kwargs.get('link')
        )
        cursor.execute(insert_query, values)
        conn.commit()
    finally:
        await close_connection_rings(conn)




# Асинхронная функция для получения диапазона цен
async def get_price_range_rings():
    conn, cursor = await create_connection_rings()
    try:
        cursor.execute("SELECT MIN(CAST(REPLACE(REPLACE(price, ',', ''), '$', '') AS INTEGER)), MAX(CAST(REPLACE(REPLACE(price, ',', ''), '$', '') AS INTEGER)) FROM rings")
        min_price, max_price = cursor.fetchone()
        return min_price, max_price
    finally:
        await close_connection_rings(conn) 
        
# Асинхронная функция для получения списка уникальных брендов
async def get_unique_brands_rings():
    conn, cursor = await create_connection_rings()
    try:
        cursor.execute("SELECT DISTINCT manufacture FROM rings WHERE manufacture IS NOT NULL")
        
        unique_brands = [row[0] for row in cursor.fetchall()]
        print(unique_brands)
        return unique_brands
    finally:
        await close_connection_rings(conn) 
        
        
                 
# Асинхронная функция для получения всех часов с возможностью установки лимита и смещения
async def get_all_rings(limit=None, offset=None):
    conn, cursor = await create_connection_rings()
    try:
        query = "SELECT id, manufacture, name, price, for_whom, conditions, images, characteristics FROM rings"
        if limit is not None:
            query += " LIMIT ?"
        if offset is not None:
            query += " OFFSET ?"
        cursor.execute(query, (limit, offset))
        rings = cursor.fetchall()
        return rings
    finally:
        await close_connection_rings(conn)

# Асинхронная функция для фильтрации часов по различным критериям
async def get_filtered_rings(filters, limit=None, offset=None):
    conn, cursor = await create_connection_rings()
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
            FROM rings
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
        rings = cursor.fetchall()
        return rings
    finally:
        await close_connection_rings(conn)




# Асинхронная функция для получения данных о часе по его идентификатору
async def get_rings_data_by_id(watch_id):
    conn, cursor = await create_connection_rings()
    try:
        cursor.execute("SELECT id, manufacture, name, price, for_whom, conditions, images, characteristics FROM rings WHERE id = ?", (watch_id,))
        rings_data = cursor.fetchone()
        return rings_data
    finally:
        await close_connection_rings(conn)