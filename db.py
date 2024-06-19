from datetime import datetime, timezone, timedelta
import sqlite3
import pandas as pd
from cryptography.fernet import Fernet

# Генерация ключа для шифрования (сделайте это один раз и сохраните ключ)
# key = Fernet.generate_key()
# with open('secret.key', 'wb') as key_file:
#     key_file.write(key)

# Загрузка ключа

def load_key():
    return open('secret.key', 'rb').read()

key = load_key()
cipher_suite = Fernet(key)

# Функция для шифрования данных
def encrypt_data(data):
    return cipher_suite.encrypt(data.encode()).decode()

# Функция для дешифрования данных
def decrypt_data(data):
    return cipher_suite.decrypt(data.encode()).decode()


# Функция для добавления клиента в таблицу clients
def add_client(c_id, c_name, c_phone,c_nik):
    conn = sqlite3.connect('base_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cleints (c_id, c_name, c_phone,c_nik)
        VALUES (?, ?, ?,?)
    ''', (c_id, encrypt_data(c_name), encrypt_data(c_phone), encrypt_data(c_nik)))
    conn.commit()
    conn.close()

# Функция для получения id мастера по его имени
def get_master_id(m_name):
    conn = sqlite3.connect('base_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m_id FROM masters WHERE m_name = ?
    ''', (m_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        raise ValueError(f'Master with name {m_name} not found')
    conn.commit()
    conn.close()

# Функция для добавления записи в таблицу services
def add_service(c_id, m_id, type, date,time):
    conn = sqlite3.connect('base_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO services (c_id, m_id, type, date,time)
        VALUES (?, ?, ?, ?,?)
    ''', (c_id, m_id, encrypt_data(type), encrypt_data(date),encrypt_data(time)))
    conn.commit()
    conn.close()


def get_client_services(c_id):
    conn = sqlite3.connect('base_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT cl.c_name, s.date, s.time, s.type, m.m_name, s_id
        FROM services s
        JOIN masters m ON s.m_id = m.m_id
        JOIN cleints cl ON s.c_id = cl.c_id
        WHERE s.c_id = ?
        ORDER BY s.date, s.time
    ''', (c_id,))
    services = cursor.fetchall()
    conn.close()
    return  [(decrypt_data(cl_name), decrypt_data(date), decrypt_data(time), decrypt_data(type), m_name, s_id) for (cl_name, date, time, type, m_name, s_id) in services]


# Пример использования
def delete_service_by_id(s_id):
    conn = sqlite3.connect('base_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM services WHERE s_id = ?
    ''', (s_id,))
    conn.commit()
    conn.close()
    print(f"Запись с s_id {s_id} удалена из таблицы services.")


def client_exists(c_id):
    conn = sqlite3.connect('base_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT EXISTS(SELECT 1 FROM cleints WHERE c_id = ?)
    ''', (c_id,))
    exists = cursor.fetchone()[0]
    conn.close()
    return bool(exists)


# Закрытие соединения
def delete_client(c_id):
    conn = sqlite3.connect('base_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM cleints WHERE c_id = ?
    ''', (c_id,))
    conn.commit()
    conn.close()
    print(f"Клиент с c_id {c_id} удален из таблицы cleints.")

# Функция для удаления записей клиента из таблицы services
def delete_client_services(c_id):
    conn = sqlite3.connect('base_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM services WHERE c_id = ?
    ''', (c_id,))
    conn.commit()
    conn.close()
    print(f"Все записи клиента с c_id {c_id} удалены из таблицы services.")



def get_master_name(m_id):
    conn = sqlite3.connect('base_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m_name FROM masters WHERE m_id = ?
    ''', (m_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None
    
def get_appointments_24h_or_more(c_id):
    conn = sqlite3.connect('base_bot.db')
    cursor = conn.cursor()

    current_datetime = datetime.now()
    end_datetime = current_datetime + timedelta(hours=7)
    end_datetime_e = current_datetime + timedelta(hours=8)

    cursor.execute('''
        SELECT date, time, s_id, type, m_id
        FROM services
        WHERE c_id = ?
    ''', (c_id,))
    
    appointments = cursor.fetchall()
    conn.close()

    decrypted_appointments = [(decrypt_data(date), decrypt_data(time), s_id, decrypt_data(type), m_id) for (date, time, s_id, type, m_id) in appointments]

    filtered_appointments = []
    for date_str, time_str, s_id, type, m_id in decrypted_appointments:
        appointment_datetime = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
        if end_datetime <= appointment_datetime <= end_datetime_e:
            filtered_appointments.append((date_str, time_str, s_id, type, m_id))

    return filtered_appointments


# def get_appointments_24h_or_more(c_id):
#     conn = sqlite3.connect('base_bot.db')
#     cursor = conn.cursor()

#     current_datetime = datetime.now()
#     end_datetime = current_datetime + timedelta(hours=18)
#     end_datetime_e = current_datetime + timedelta(hours=19)
    

#     end_datetime_str = end_datetime.strftime('%Y-%m-%d %H:%M')
#     end_datetime_str2 = end_datetime_e.strftime('%Y-%m-%d %H:%M')


#     cursor.execute('''
#         SELECT date, time, s_id, type, m_id
#         FROM services
#         WHERE c_id = ? AND datetime(date || ' ' || time) >= datetime(?) AND datetime(date || ' ' || time) <= datetime(?)
#     ''', (c_id, end_datetime_str, end_datetime_str2))
    
#     appointments = cursor.fetchall()
#     conn.close()
#     return appointments

def get_admin_data():
    conn = sqlite3.connect('base_bot.db') 
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            c.c_name AS "Имя клиента",
            c.c_phone AS "Номер клиента",
            c.c_nik AS "Ник в Телеграмме",
            m.m_name AS "Имя мастера",
            s.type AS "Услуга",
            s.date AS "Дата",
            s.time AS "Время"
        FROM cleints c
        JOIN services s ON c.c_id = s.c_id
        JOIN masters m ON s.m_id = m.m_id
    ''')
    data = cursor.fetchall()
    conn.close()

    # Декодирование данных
    decoded_data = []
    for row in data:
        decoded_row = (
            decrypt_data(row[0]),  # c_name
            decrypt_data(row[1]),  # c_phone
            decrypt_data(row[2]),  # c_nik
            row[3],                # m_name (не закодировано)
            decrypt_data(row[4]),  # type
            decrypt_data(row[5]),  # date
            decrypt_data(row[6])   # time
        )
        decoded_data.append(decoded_row)

    # Создание DataFrame из декодированных данных
    df = pd.DataFrame(decoded_data, columns=[
        "Имя клиента",
        "Номер клиента",
        "Ник в Телеграмме",
        "Имя мастера",
        "Услуга",
        "Дата",
        "Время"
    ])
    
    return df
# def get_admin_data():
#     conn = sqlite3.connect('base_bot.db') 
#     cursor = conn.cursor()
#     cursor.execute('''
#         SELECT
#             c.c_name AS "Имя клиента",
#             c.c_phone AS "Номер клиента",
#             c.c_nik AS "Ник в Телеграмме",
#             m.m_name AS "Имя мастера",
#             s.type AS "Услуга",
#             s.date AS "Дата",
#             s.time AS "Время"
#         FROM cleints c
#         JOIN services s ON c.c_id = s.c_id
#         JOIN masters m ON s.m_id = m.m_id
#     ''')
#     data = cursor.fetchall()
#     conn.close()
#     df = pd.DataFrame(data, columns=[
#         "Имя клиента",
#         "Номер клиента",
#         "Ник в Телеграмме",
#         "Имя мастера",
#         "Услуга",
#         "Дата",
#         "Время"
#     ])
#     return df


# def get_client_services_by_date(m_id, date):
#     conn = sqlite3.connect('base_bot.db')
#     cursor = conn.cursor()

   
#     if '-' not in date:  # YYYY
#         query = '''
#             SELECT cl.c_name, cl.c_nik, cl.c_phone, s.date, s.time, s.type, m.m_name
#             FROM services s
#             JOIN masters m ON s.m_id = m.m_id
#             JOIN cleints cl ON s.c_id = cl.c_id
#             WHERE s.m_id = ? AND substr(s.date, 1, 4) = ?
#             ORDER BY s.date, s.time
#         '''
#     elif date.count('-') == 1:  # YYYY-MM
#         query = '''
#             SELECT cl.c_name, cl.c_nik, cl.c_phone, s.date, s.time, s.type, m.m_name
#             FROM services s
#             JOIN masters m ON s.m_id = m.m_id
#             JOIN cleints cl ON s.c_id = cl.c_id
#             WHERE s.m_id = ? AND substr(s.date, 1, 7) = ?
#             ORDER BY s.date, s.time
#         '''
#     else:  # YYYY-MM-DD
#         query = '''
#             SELECT cl.c_name, cl.c_nik, cl.c_phone, s.date, s.time, s.type, m.m_name
#             FROM services s
#             JOIN masters m ON s.m_id = m.m_id
#             JOIN cleints cl ON s.c_id = cl.c_id
#             WHERE s.m_id = ? AND s.date = ?
#             ORDER BY s.time
#         '''
#     cursor.execute(query, (m_id, date))
#     services = cursor.fetchall()
#     conn.close()
#     return services
def get_client_services_by_date(m_id, date):
    conn = sqlite3.connect('base_bot.db')
    cursor = conn.cursor()

    # Извлекаем все записи для данного мастера
    cursor.execute('''
        SELECT cl.c_name, cl.c_nik, cl.c_phone, s.date, s.time, s.type, m.m_name
        FROM services s
        JOIN masters m ON s.m_id = m.m_id
        JOIN cleints cl ON s.c_id = cl.c_id
        WHERE s.m_id = ?
        ORDER BY s.date, s.time
    ''', (m_id,))
    services = cursor.fetchall()
    conn.close()

    # Фильтруем и декодируем данные
    filtered_services = []
    for row in services:
        decrypted_date = decrypt_data(row[3])
        if (('-' not in date and decrypted_date.startswith(date)) or 
            (date.count('-') == 1 and decrypted_date.startswith(date)) or 
            (date.count('-') == 2 and decrypted_date == date)):
            
            decrypted_row = (
                decrypt_data(row[0]),  # cl.c_name
                decrypt_data(row[1]),  # cl.c_nik
                decrypt_data(row[2]),  # cl.c_phone
                decrypted_date,         # s.date
                decrypt_data(row[4]),  # s.time
                decrypt_data(row[5]),  # s.type
                row[6]                 # m.m_name (не закодировано)
            )
            filtered_services.append(decrypted_row)

    return filtered_services

def master_exists(m_id):
    conn = sqlite3.connect('base_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT EXISTS(SELECT 1 FROM masters WHERE m_id = ?)
    ''', (m_id,))
    exists = cursor.fetchone()[0]
    conn.close()
    return bool(exists)

# def get_client_name(c_id):
#     conn = sqlite3.connect('base_bot.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         SELECT c_name FROM cleints WHERE c_id = ?
#     ''', (c_id,))
#     result = cursor.fetchone()
#     conn.close()
#     if result:
#         return result[0]
#     else:
#         return None
def get_client_name(c_id):
    conn = sqlite3.connect('base_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c_name FROM cleints WHERE c_id = ?
    ''', (c_id,))
    result = cursor.fetchone()
    conn.close()
    if result:

        decrypted_name = decrypt_data(result[0])
        return decrypted_name
    else:
        return None   
    
# def get_last_client_service(m_id):
#     conn = sqlite3.connect('base_bot.db')
#     cursor = conn.cursor()

#     cursor.execute('''
#         SELECT cl.c_name, s.date, s.time, s.type, m.m_name, s_id
#         FROM services s
#         JOIN masters m ON s.m_id = m.m_id
#         JOIN cleints cl ON s.c_id = cl.c_id
#         WHERE s.m_id = ?
#         ORDER BY s.date DESC, s.time DESC
#         LIMIT 1
#     ''', (m_id,))
    
#     last_service = cursor.fetchone()
#     conn.close()
#     return last_service
    
def get_last_client_service(m_id):
    conn = sqlite3.connect('base_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT cl.c_name, s.date, s.time, s.type, m.m_name, s_id
        FROM services s
        JOIN masters m ON s.m_id = m.m_id
        JOIN cleints cl ON s.c_id = cl.c_id
        WHERE s.m_id = ?
        ORDER BY s.date DESC, s.time DESC
        LIMIT 1
    ''', (m_id,))
    
    last_service = cursor.fetchone()
    conn.close()

    if last_service:
        # Decrypt encoded fields
        decrypted_name = decrypt_data(last_service[0])  # cl.c_name
        decrypted_date = decrypt_data(last_service[1])  # s.date
        decrypted_time = decrypt_data(last_service[2])  # s.time
        decrypted_type = decrypt_data(last_service[3])  # s.type
        
        # Replace encrypted fields with decrypted values
        last_service = (
            decrypted_name,
            decrypted_date,
            decrypted_time,
            decrypted_type,
            last_service[4],  # m.m_name (not encrypted)
            last_service[5]   # s_id (not encrypted)
        )
    
    return last_service

# Пример использования функций
if __name__ == '__main__':
    #add_client(288775517, "c_name", "c_phone","c_nik")
    #add_service(288775517, 288775517, "вавав", '2024-06-07','13:00')
   print( get_last_client_service(288775517))
   # print(get_all_appointments(288775517))
    #print(get_last_client_service('288775517'))

   # s_id_to_delete = 8  # Пример s_id для удаления
    
   # delete_service_by_id(s_id_to_delete)

    # c_id_to_delete = 288775517  # Пример c_id для удаления    
    # print (master_exists(c_id_to_delete))
   
    # delete_client_services(c_id_to_delete)  # Сначала удаляем записи клиента
    # delete_client(c_id_to_delete)  # Затем удаляем самого клиен