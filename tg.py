
import datetime
import json
import re
import telebot
import sys
import threading
import telegram
sys.path.append('C:/Users/Professional/Desktop/diploma/botcalendar.py')
from telebot import apihelper
import botcalendar
from telebot import types
from datetimerange import DateTimeRange
from collections import namedtuple
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

from elegram_bot_calendar_m import *
from dateutil.relativedelta import relativedelta
import db
import pandas as pd
from datetime import *

token = '6307067319:AAFViRxf6VvEpKu-CXxJhSpUgS3YJQzzMQU'
bot = telebot.TeleBot('6307067319:AAFViRxf6VvEpKu-CXxJhSpUgS3YJQzzMQU',num_threads=5)

all_target_descriptions = ['Оксана Самойлова', 'Дмитрий Васильков', 'Алексей Бочкарев', 'Алексей Вавилов', 'Мария Гончарова']
user_data = {}
def get_user_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
                'appointment_details': {
                    'data': '',
                    'time_service': '',
                    'selected_time': '',
                    'service': '',
                    'master': '',
                    'user_id': '0',
                    'user_nik': ''
                },
                'masterm': False,
                'datem': False,
                'servicem': False,
                'key_master':False,
                'rez':None,
                'msg':None,
                'b':None,
                'a':None,
                'kx':1,
                'name_cleint':None,
                'phone_client':None,
                'mas_month':False,
                'mas_year':False,
                'mas_day':False,
                'selected_time_slot_start':0,
                'selected_time_slot_end':0,
                'zanyat_rez':0,
                'new_client':None,
                'times':[]
            }
    return user_data[user_id]


names_to_numbers = {
    'Оксана Самойлова': 1,
    'Дмитрий Васильков': 2,
    'Алексей Бочкарев': 3,
    'Алексей Вавилов': 4,
    'Мария Гончарова': 5
}


#меню
def menu(chat_id, user_id):
    user_info = get_user_data(user_id)   
    markup = types.InlineKeyboardMarkup()
    if user_info['masterm'] ==False:
        
        btn21 = types.InlineKeyboardButton("Выбрать специалиста",callback_data='master')
        markup.row(btn21)
    if user_info['datem'] ==False:
        
        btn22 = types.InlineKeyboardButton("Выбрать дату и время",callback_data='date')
        markup.row(btn22)
    if user_info['servicem']== False:
       
        btn23 = types.InlineKeyboardButton("Выбрать услугу",callback_data='service')
        markup.row(btn23)
    if user_info['masterm'] == False or user_info['datem']== False or user_info['servicem']== False:
        bot.send_message(
            chat_id, text=("Выберите дейтсвие ниже 👇"), reply_markup=markup)
        

def startm(m):

    calendar, step = DetailedTelegramCalendar(calendar_id=2,locale='ru').build()
    bot.send_message(m.chat.id,
                     f"Выберите",
                     reply_markup=calendar)

    
@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def cal(c):
    result, key, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').process(c.data)
    user_id = c.message.chat.id
    user_info = get_user_data(user_id)
    try:
        data = json.loads(key)
        inline_keyboard = data.get('inline_keyboard', [])
        index_of_double_arrow = None
        for row in inline_keyboard:
            for i, item in enumerate(row):
                if isinstance(item, dict) and item.get('text') == ">>":
                    index_of_double_arrow = (inline_keyboard.index(row), i)
                    break
            if index_of_double_arrow:
                break

        if index_of_double_arrow:
            row_index, col_index = index_of_double_arrow
            if col_index - 1 >= 0 and col_index - 1 < len(inline_keyboard[row_index]):
                next_item = inline_keyboard[row_index][col_index - 1]
                if isinstance(next_item, dict) and 'callback_data' in next_item:
                    callback_data_to_use = next_item['callback_data']            
                    pattern = r'cbcal_2_g_([my])_(\d{4})_(\d+)'
                    
                    match = re.search(pattern, callback_data_to_use)
                    if match:
                        identifier = match.group(1)
                        year = match.group(2)
                        if identifier == 'y':
                            resulty = year
                            if user_info['mas_month'] == False and user_info['mas_day']==False:
                                result = resulty
                        elif identifier == 'm':
                            month = match.group(3)
                            resultm = f"{year}-{month.zfill(2)}"
                            if user_info['mas_year'] == False and user_info['mas_day']==False:
                                result = resultm
                    else:
                        print("Шаблон не найден")
                else:
                    print("Следующий элемент не содержит 'callback_data'")
            else:
                print("Следующий элемент находится за пределами текущей строки")
        else:
            print("Не найден элемент с текстом '>>'")
    except json.JSONDecodeError:
        print("Ошибка декодирования JSON")
    except KeyError as e:
        print(f"Ошибка ключа: {e}")
    except TypeError as e:
        print(f"Ошибка типа: {e}")

    if not result and key:
        bot.edit_message_text(f"Выберите",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    if result:
        bot.edit_message_text(f"Вы выбрали {result}",
                              c.message.chat.id,
                              c.message.message_id)
        
        
       
        result1=str(result)
        mas_id=db.get_master_id(db.get_master_name(int(c.message.chat.id)))
        get_cleint(c.message, result1,mas_id)

def get_cleint(message,date,m_id):
        chat_id = message.chat.id
        client_services = db.get_client_services_by_date(m_id, date) 
        if client_services:
            for service in client_services:
                    client_name,client_nik, client_phone,service_date, service_time, service_type, master_name = service
                    message_text = f"Имя клиента: {client_name} ({client_nik})\nНомер телефона: {client_phone}\nПроцедура: {service_type}\nДата записи: {service_date}\nВремя записи: {service_time}"
                    bot.send_message(chat_id, message_text)
        else:
            bot.send_message(chat_id, f"Нет записей {date}.")




#запуск календаря         
def start_calendar(m):
    today = date.today()
    next_month = today + relativedelta(months=2)
    max_date = next_month.replace(day=1) - relativedelta(days=1)
    calendar, step = WMonthTelegramCalendar(locale='ru', min_date=date.today(), max_date=max_date).build()
    bot.send_message(m.chat.id, f"Выберите", reply_markup=calendar)

@bot.callback_query_handler(func=WMonthTelegramCalendar.func())
def cal(c):
    user_id = c.message.chat.id
    user_info = get_user_data(user_id)
    today = date.today()
    next_month = today + relativedelta(months=2)
    max_date = next_month.replace(day=1) - relativedelta(days=1)
    result, key, step = WMonthTelegramCalendar(locale='ru',min_date=date.today(),max_date=max_date).process(c.data)
    user_info['rez'] = result
    if not result and key:  
            bot.edit_message_text(f"Выберите день", c.message.chat.id, c.message.message_id, reply_markup=key) 
    elif result:
        result_m = str(result)
        parts = result_m.split('-')  
        month_day = parts[1] + '-' + parts[2]
        if user_info['masterm'] ==False:
            free_time_slots = botcalendar.calendar1.get_free_time_slots(botcalendar.calen, all_target_descriptions, result_m,user_info,user_info['appointment_details']['time_service'])
        elif user_info['masterm'] ==True:
            master_name = user_info['appointment_details']['master']    
            free_time_slots = botcalendar.calendar1.get_free_time_slots(botcalendar.calen, master_name, result_m,user_info,user_info['appointment_details']['time_service'])
        if free_time_slots == None:
            if not user_info['b']:
                bot.answer_callback_query(c.id)
                user_info['msg'] = bot.send_message(c.message.chat.id, text=f"На {month_day} нет свободного времени для записи. Выберите другую дату.", reply_markup=types.InlineKeyboardMarkup(row_width=4))
                user_info['a'] =1
                user_info['b']=1
                bot.answer_callback_query(c.id)
            elif user_info['b']:
                try:
                     user_info['msg'] = bot.edit_message_text(f"На {month_day} нет свободного времени для записи. Выберите другую дату.", c.message.chat.id, user_info['msg'].message_id,reply_markup=types.InlineKeyboardMarkup(row_width=4))
                except telebot.apihelper.ApiTelegramException as e:
                    print(f"Ignoring error: {e}")
        else:
            reply_markup = create_buttons_for_time_slots(free_time_slots) 
            if not user_info['a']:
                user_info['msg'] = bot.send_message(c.message.chat.id, text=f"Выберите время {month_day}", reply_markup=reply_markup)
                user_info['a'] =1
                bot.answer_callback_query(c.id)
            elif user_info['a']:
                try:
                    bot.answer_callback_query(c.id)
                    user_info['msg'] = bot.edit_message_text(f"Выберите время {month_day}", c.message.chat.id, user_info['msg'].message_id, reply_markup=reply_markup)
                    bot.answer_callback_query(c.id)
                except telebot.apihelper.ApiTelegramException as e:
                    print(f"Ignoring error: {e}")
            bot.answer_callback_query(c.id)
            bot.edit_message_reply_markup(c.message.chat.id, user_info['msg'].message_id, reply_markup=reply_markup)
            bot.answer_callback_query(c.id)

def create_buttons_for_time_slots(free_time_slots):
    markup = types.InlineKeyboardMarkup(row_width=4)  
    buttons = [types.InlineKeyboardButton(time_slot, callback_data=f"selected_time:{time_slot}") for time_slot in free_time_slots]    
    for i in range(0, len(buttons), 4):
        if i+3 < len(buttons):
            markup.row(*buttons[i:i+4])
        else:
            remaining_buttons = buttons[i:]
            markup.row(*remaining_buttons)
    return markup


def start_create_buttons_for_master():
    markup = types.InlineKeyboardMarkup(row_width=4)
    buttons = []
    current_time = datetime.strptime("11:00", "%H:%M")
    end_time = datetime.strptime("21:00", "%H:%M")

    while current_time <= end_time:
        buttons.append(types.InlineKeyboardButton(current_time.strftime("%H:%M"), callback_data=f"start_selected_time_master:{current_time.strftime('%H:%M')}"))
        current_time += timedelta(hours=1)
    for i in range(0, len(buttons), 4):
        if i+3 < len(buttons):
            markup.row(*buttons[i:i+4]) 
        else:
            remaining_buttons = buttons[i:]
            markup.row(*remaining_buttons)
    return markup 

def end_create_buttons_for_master():
    markup = types.InlineKeyboardMarkup(row_width=4)
    buttons = []
    current_time = datetime.strptime("11:00", "%H:%M")
    end_time = datetime.strptime("21:00", "%H:%M")

    while current_time <= end_time:
        buttons.append(types.InlineKeyboardButton(current_time.strftime("%H:%M"), callback_data=f"end_selected_time_master:{current_time.strftime('%H:%M')}"))
        current_time += timedelta(hours=1)

    for i in range(0, len(buttons), 4):
        if i+3 < len(buttons):
            markup.row(*buttons[i:i+4])  
        else:
            remaining_buttons = buttons[i:]
            markup.row(*remaining_buttons)
    return markup 

#кнопка мастеров
def create_buttons_masters(list_of_masters):
    markup = types.InlineKeyboardMarkup(row_width=1)  
    for name_master in list_of_masters:
        button = types.InlineKeyboardButton(name_master, callback_data=f'name_master:{name_master}')
        markup.add(button)
    return markup

def show_client_services(chat_id, c_id, index=None, message_id=None):
    services = db.get_client_services(c_id)
    
    if not services:
        bot.send_message(chat_id, "У вас нет записей.")
        return

    if index is None:
        index = len(services) - 1
    else:
        index = min(len(services) - 1, max(0, index))

    service = services[index]
    message_text = (f"*Профиль: {service[0]}*\n\n"
                    f"🔔 Данные о записи: 🔔\n\n"
                    f"📆 Дата: {service[1]}\n"
                    f"🕐 Время: {service[2]}\n"
                    f"📌 Процедура: {service[3]}\n"
                    f"👤 Мастер: {service[4]}\n\n"
                    f"_Страница {len(services) - index}/{len(services)}_"
                    )
    
    reply_markup = types.InlineKeyboardMarkup()
    if botcalendar.calendar1.is_event_within_24_hours(botcalendar.calen, service[1], service[2], service[4]):
       
        reply_markup.add(types.InlineKeyboardButton("Отменить запись", callback_data=f'delete,{service[1]},{service[2]},{service[4]},{service[5]}'))
    if index < len(services) - 1:
        reply_markup.add(types.InlineKeyboardButton("<< Назад", callback_data=f'previous:{c_id}:{index+1}'))
    if index > 0:
        reply_markup.add(types.InlineKeyboardButton("Вперед >>", callback_data=f'next:{c_id}:{index-1}'))

    if message_id:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, message_text, reply_markup=reply_markup, parse_mode="Markdown")


def startm1(m):
    calendar, step = DetailedTelegramCalendar(calendar_id=3,locale='ru',min_date=date.today()).build()
    bot.send_message(m.chat.id,
                     f"Выберите",
                     reply_markup=calendar)

@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=3))
def cal(c):
    user_id = c.message.chat.id
    user_info = get_user_data(user_id)
    result, key, step = DetailedTelegramCalendar(calendar_id=3, locale='ru', min_date=date.today()).process(c.data)
    if not result and key:
        bot.edit_message_text(f"Выберите",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    if result:
        bot.edit_message_text(f"Вы выбрали {result}",
                              c.message.chat.id,
                              c.message.message_id)
        
        user_info['zanyat_rez'] = result
        markup = types.InlineKeyboardMarkup()
        btn22 = types.InlineKeyboardButton("Да",callback_data='da_zanyat')
        btn23 = types.InlineKeyboardButton("Нет",callback_data='net_zanyat')
        markup.add(btn22,btn23)
        bot.send_message(c.message.chat.id, text=f'Отметить весь выбранный день как занятый?', reply_markup=markup)
     

#старт
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_info = get_user_data(user_id)
    user_info['appointment_details']['user_nik'] = message.from_user.username or "нету ника"
    user_info['appointment_details']['user_id'] = user_id
   
    markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton("📍Профиль📍")
    btn22 = types.KeyboardButton("👋Записаться на прием👋")

    task_thread = threading.Thread(target=periodic_task_master, args=(user_id,))
    task_thread.daemon = True
    task_thread.start()
    task_thread = threading.Thread(target=periodic_task, args=(user_id,))
    task_thread.daemon = True
    task_thread.start()
    if user_id == 288775517:
        btn24 = types.KeyboardButton("💻Кабинет администатора💻")
        markup1.add(btn24)
    if db.master_exists((int(message.from_user.id))):
        btn12 = types.KeyboardButton("🖊Личный кабинет мастера🖊")
        markup1.add(btn12, btn1, btn22)  
    else:
        markup1.add(btn1, btn22)

    bot.send_message(message.chat.id, text="* Здравствуйте, {0.first_name}!*\n\n•Чтобы записаться на прием нажми на кнопку \n*👋Записаться на прием👋*.\n\n•Для просмотра истории посещений или отмены записи нажми на кнопку *📍Профиль📍* \n\n ❗ ⠀Важно⠀❗ \nЕсли кнопки не появились нажмите на 🎛 квадратик с четырмя точками (он находится рядом с выбором эмодзи 🙂 в строке отправки сообщений)".format(
        message.from_user), reply_markup=markup1, parse_mode="Markdown")


#самое начало диалога 
@bot.message_handler(content_types=['text'])
def func(message):
    
    user_id = message.from_user.id
    user_info = get_user_data(user_id)
    user_info['appointment_details']['user_nik'] = message.from_user.username or "нету ника"
    user_info['appointment_details']['user_id'] = user_id


    if (message.text =='💻Кабинет администатора💻'):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn1 = types.KeyboardButton("Получить таблицу всех записей")
        button4=types.KeyboardButton("В меню")
        markup.add(btn1)
        markup.add(button4)
        bot.send_message(message.chat.id, text=f'Личный кабинет администратора', reply_markup=markup)

    if (message.text =='Получить таблицу всех записей'):
        admin_data = db.get_admin_data()
        admin_data.to_csv('admin_data.csv', index=False)
        with open('admin_data.csv', 'r', encoding='utf-8') as file:
            bot.send_document(message.chat.id, file) 
   
    if (message.text =='В меню'):

        markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn1 = types.KeyboardButton("📍Профиль📍")
        btn22 = types.KeyboardButton("👋Записаться на прием👋")
       
        if user_id == 288775517:
            btn24 = types.KeyboardButton("💻Кабинет администатора💻")
            markup1.add(btn24)
        if db.master_exists((int(message.from_user.id))):
            btn12 = types.KeyboardButton("🖊Личный кабинет мастера🖊")
            markup1.add(btn12, btn1, btn22)  
        else:
            markup1.add(btn1, btn22)

        bot.send_message(message.chat.id, text="* Здравствуйте, {0.first_name}!*\n\n•Чтобы записаться на прием нажми на кнопку \n*👋Записаться на прием👋*.\n\n•Для просмотра истории посещений или отмены записи нажми на кнопку *📍Профиль📍* \n\n ❗ ⠀Важно⠀❗ \nЕсли кнопки не появились нажмите на 🎛 квадратик с четырмя точками (он находится рядом с выбором эмодзи 🙂 в строке отправки сообщений)".format(
        message.from_user), reply_markup=markup1, parse_mode="Markdown")


    
    if (message.text == "🖊Личный кабинет мастера🖊") or (message.text == "Назад") and db.master_exists(int(user_info['appointment_details']['user_id'])):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        chat_id = message.chat.id

        button1 = types.KeyboardButton("Посмотреть записи")
        button2 = types.KeyboardButton("Настроить свободные слоты")
        button4=types.KeyboardButton("В меню")
        markup.add(button1, button2)
        markup.add(button4)

        bot.send_message(chat_id, text=f'Личный кабинет мастера {db.get_master_name(int(message.from_user.id))}', reply_markup=markup)
    
    if (message.text =="Посмотреть записи"):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
            chat_id = message.chat.id    
            button1 = types.KeyboardButton("За год")
            button2 = types.KeyboardButton("За месяц")
            button3 = types.KeyboardButton("За день")
            button4=types.KeyboardButton("Назад")
            markup.add(button1, button2,button3)
            markup.add(button4)

            bot.send_message(chat_id, text=f'Личный кабинет мастера {db.get_master_name(int(message.from_user.id))}', reply_markup=markup)
    
    if (message.text =="Настроить свободные слоты"):

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        button1 = types.KeyboardButton("Отметить занятые слоты")      
        chat_id = message.chat.id  
        button4=types.KeyboardButton("Назад")
        markup.add(button1)
        markup.add(button4)

        bot.send_message(chat_id, text=f'Личный кабинет мастера {db.get_master_name(int(message.from_user.id))}', reply_markup=markup)
    
    if message.text =='Отметить занятые слоты':
        
        startm1(message)
  
    if message.text == "За год":
        user_info['mas_month'] = False
        user_info['mas_day']=False
        user_info['mas_year'] = True    
        startm(message)


    elif message.text == "За месяц":
        user_info['mas_month'] = True
        user_info['mas_day']=False
        user_info['mas_year'] = False 
        startm(message)

    elif message.text == "За день":
        user_info['mas_month'] = False
        user_info['mas_day']=True 
        user_info['mas_year'] = False 
        startm(message)
            
    if (message.text =="📍Профиль📍"):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
            chat_id = message.chat.id
            btn22 = types.KeyboardButton("Где мы находимся?")
            btn23 = types.KeyboardButton("Мои записи")
            button4=types.KeyboardButton("В меню")
            markup.add(btn22,btn23)
            markup.add(button4)
            bot.send_message(chat_id, text=f'Профиль клиента', reply_markup=markup)

    if (message.text =="Мои записи"):
            chat_id = message.chat.id
            user_id = message.from_user.id 
            bot.send_message(chat_id, text=f'Если вы хотите отменить запись, то нажмите на кнопку "*Отменить запись*". \nЕсли до записи осталось менее 24 часов, то кнопки не будет.',  parse_mode="Markdown") 
            show_client_services(chat_id, user_id)  

    if(message.text == "Где мы находимся?"):
        chat_id = message.chat.id
        media_group = []
        with open(f'C:/Users/Professional/Desktop/diploma/photo_masters/adres2.jpg', 'rb') as photo:
                        photo_content = photo.read()
                        media_group.append(types.InputMediaPhoto(media=photo_content))
        bot.send_media_group(chat_id, media_group)
        bot.send_message(chat_id, text=f'Наш адрес: Советская 18, 9 этаж, 903 кабинет')

    if(message.text == "👋Записаться на прием👋"):
        user_info['masterm'] = False
        user_info['datem'] = False
        user_info['datem'] = False
        
        user_info['appointment_details']['master'] = ''
        user_info['appointment_details']['data'] = ''
        user_info['appointment_details']['time_service'] = ''
        user_info['appointment_details']['selected_time'] = ''
        user_info['appointment_details']['service'] = ''
        user_info['kx']=1
        menu(message.chat.id,user_id )   
         

    

@bot.callback_query_handler(func=lambda callback: True)
       
def callback_handler(callback):

   


    user_id = callback.message.chat.id
    chat_id = callback.message.chat.id
    user_info = get_user_data(user_id)

    if callback.data.startswith('delete,'):
        
        reply_markup = types.InlineKeyboardMarkup()
        message_id = callback.message.message_id
        selected_time = user_info['appointment_details']['selected_time']
        data =callback.data.split(',')
        db.delete_service_by_id(data[4])
        date=data[1]
        time=data[2]
        description=data[3]
        event_id=botcalendar.calendar1.get_events_id(botcalendar.calen, date, time, description)
        if botcalendar.calendar1.delete_event(botcalendar.calen, event_id):
           bot.edit_message_text(chat_id=callback.message.chat.id, message_id=message_id,text= "Запись отменена",reply_markup=reply_markup) 
    
    if callback.data.startswith('previous:') or callback.data.startswith('next:'):
        message_id = callback.message.message_id
        data =callback.data.split(':')
        direction = data[0]
        c_id = int(data[1])
        index = int(data[2])
        services = db.get_client_services(callback.message.from_user.id)

        if direction == 'previous':
            if index < len(services) - 1:
                  show_client_services(callback.message.chat.id, c_id, index, message_id)
            else:
                show_client_services(callback.message.chat.id, c_id, index, message_id)
        elif direction == 'next':
            if index > 0:
                show_client_services(callback.message.chat.id, c_id, index, message_id)
            else:
                show_client_services(callback.message.chat.id, c_id, index, message_id)
    
    if callback.data == 'da_zanyat':
        reply_markup = types.InlineKeyboardMarkup()
        message_id = callback.message.message_id
        botcalendar.calendar1.create_event(botcalendar.calen,f"выходной:{db.get_master_name(user_info['appointment_details']['user_id'])}", db.get_master_name(user_info['appointment_details']['user_id']),user_info['zanyat_rez'],user_info['zanyat_rez'],'00:00', '23:59', names_to_numbers.get(db.get_master_name(callback.message.chat.id)))
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=message_id,text= f"Весь {user_info['zanyat_rez']} отмечен как занятый",reply_markup=reply_markup) 
    
    if  callback.data == 'net_zanyat':
        reply_markup = types.InlineKeyboardMarkup()
        message_id = callback.message.message_id
        reply_markup=start_create_buttons_for_master()
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=message_id,text= f"Выберете время начала занятого слота ",reply_markup=reply_markup) 
    
    if callback.data.startswith('start_selected_time_master:'):
        user_info['selected_time_slot_start'] = callback.data.replace('start_selected_time_master:', '')  # Получаем выбранный временной слот
        message_id = callback.message.message_id
        reply_markup = types.InlineKeyboardMarkup()
        reply_markup=end_create_buttons_for_master()
        bot.send_message(callback.message.chat.id, f"Выберете время окончания занятого слота",reply_markup=reply_markup)

    if callback.data.startswith('end_selected_time_master:'):
        markup = types.InlineKeyboardMarkup()  
        user_info['selected_time_slot_end'] = callback.data.replace('end_selected_time_master:', '')  
        message_id = callback.message.message_id
        btn1 = types.InlineKeyboardButton("Да", callback_data='da_master_select')
        btn2 = types.InlineKeyboardButton("Нет", callback_data='net_zanyat')
        markup.add(btn1,btn2)

        bot.edit_message_text(chat_id=callback.message.chat.id,message_id=message_id, text=f"Дата:{user_info['zanyat_rez']}\n Начало:{user_info['selected_time_slot_start']}\n Конец:{user_info['selected_time_slot_end']}\nВсе верно?",reply_markup=markup)
    
    if callback.data == 'da_master_select':
        reply_markup = types.InlineKeyboardMarkup()
        message_id = callback.message.message_id
        botcalendar.calendar1.create_event(botcalendar.calen,f"выходной:{db.get_master_name(user_info['appointment_details']['user_id'])}", db.get_master_name(user_info['appointment_details']['user_id']),user_info['zanyat_rez'],user_info['zanyat_rez'],user_info['selected_time_slot_start'], user_info['selected_time_slot_end'], names_to_numbers.get(db.get_master_name(callback.message.chat.id)))
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=message_id,text= f"Слот {user_info['zanyat_rez']} c {user_info['selected_time_slot_start']} до {user_info['selected_time_slot_end']} отмечен как занятый",reply_markup=reply_markup) 
    
    if callback.data.startswith('selected_time:'):
        user_info['datem'] = True
        selected_time_slot = callback.data.replace('selected_time:', '')  
        bot.send_message(callback.message.chat.id, f"Вы выбрали: {user_info['rez']} - {selected_time_slot}")
        user_info['appointment_details']['selected_time'] = selected_time_slot
        user_info['appointment_details']['data'] = user_info['rez']
        menu(chat_id,user_id)


        
    #нажали на кнопку выбора мастера 
    if callback.data == 'master':
        user_info['masterm'] = False
        user_info['key_master'] = False
        chat_id = callback.message.chat.id
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        bot.send_message(chat_id, 'Наши мастера:')

        if  user_info['datem']:
            data_my =  user_info['appointment_details']['data']
            time_my =  user_info['appointment_details']['selected_time']
            new_time_my=time_my

            if user_info['servicem']:
                minutes =  user_info['appointment_details']['time_service']         
                current_hours, current_minutes = map(int, time_my.split(':'))
                new_minutes = current_minutes + (int(minutes)-1)
                new_hours = current_hours + new_minutes // 60
                new_minutes %= 60
                new_time_my = '{:02d}:{:02d}'.format(new_hours, new_minutes)

            target_datetime = f'{data_my}T{time_my}:00+07:00'    
            end_date=f'{data_my}T{ new_time_my}:00+07:00' 
            available_masters = []
            busy_descriptions =botcalendar.calendar1.get_busy_descriptions(botcalendar.calen, target_datetime,end_date)
            
            for master in all_target_descriptions:
                if master not in busy_descriptions:
                    available_masters.append(master)
           
            if available_masters:
                markup=create_buttons_masters(available_masters)    
                media_group = []
                for master in available_masters:
                    with open(f'C:/Users/Professional/Desktop/diploma/photo_masters/{master}.jpg', 'rb') as photo:
                        photo_content = photo.read()
                        media_group.append(types.InputMediaPhoto(media=photo_content))
                bot.send_media_group(chat_id, media_group)
                bot.send_message(chat_id, text="Выберите мастера", reply_markup=markup)
            else:
                bot.send_message(chat_id, "Извините, все мастера заняты в это время. Пожалуйста, выберите другое время или услугу.")
                user_info['key_master'] = True
                
        else:
            markup=create_buttons_masters(all_target_descriptions)
            media_group = []
            for master in all_target_descriptions:
                    with open(f'C:/Users/Professional/Desktop/diploma/photo_masters/{master}.jpg', 'rb') as photo:
                        photo_content = photo.read()
                        media_group.append(types.InputMediaPhoto(media=photo_content))
            bot.send_media_group(chat_id, media_group)
            bot.send_message(chat_id, text="Выберите мастера", reply_markup=markup)

        if user_info['key_master']:     
            markup = types.InlineKeyboardMarkup()           
            btn22 = types.InlineKeyboardButton("Выбрать дату и время",callback_data='date')
            markup.add(btn22)
            btn23 = types.InlineKeyboardButton("Выбрать услугу",callback_data='service')
            markup.add(btn23)
            bot.send_message(
                            chat_id, text=("Выберите дейтсвие ниже 👇"), reply_markup=markup)
    #выбрали мастера
    if callback.data.startswith('name_master:'):
        chat_id = callback.message.chat.id
        name_master = callback.data.replace('name_master:', '')  
        bot.send_message(callback.message.chat.id, f"Вы выбрали: {name_master}")
        user_info['masterm'] = True
        user_info['appointment_details']['master'] = name_master
        menu(chat_id,user_id ) 
        
    #нажали на кнопку даты   
    if callback.data == 'date':
        user_info['rez']=None
        user_info['msg']=None
        user_info['b']=None
        user_info['a']=None
        user_info['datem'] = False
        user_info['appointment_details']['selected_time'] =""
        user_info['appointment_details']['data'] =""
        start_calendar(callback.message)
            
    #нажали на кнопку выбрать услугу
    if callback.data == 'service':
        user_info['servicem']=False
        chat_id = callback.message.chat.id
        bot.send_message(chat_id, 'Выберите услугу')
        if user_info['datem'] == True and user_info['masterm']:
            master_name = user_info['appointment_details']['master']
            data_my =  user_info['appointment_details']['data']
            time_my = user_info['appointment_details']['selected_time']
            with open('dataservice.txt', 'r', encoding='utf-8') as file:
                services_data = file.readlines()    
            services = ''
            minutes = 0
            price = 0
            markup = types.InlineKeyboardMarkup(row_width=1)
            for line in services_data:
                service, minutes,price = line.strip().split(':')
                services=service.strip()
                services=services.replace("+", "")
                current_hours, current_minutes = map(int, time_my.split(':'))
                new_minutes = current_minutes + (int(minutes)-1)
                new_hours = current_hours + new_minutes // 60
                new_minutes %= 60
                new_time_end = '{:02d}:{:02d}'.format(new_hours, new_minutes)
                current_date_str = data_my.strftime('%Y-%m-%d')   
                if int(minutes) >= 60:
                    hours = int(minutes) // 60
                    remaining_minutes = int(minutes) % 60
                    if remaining_minutes > 0:
                        formatted_time = f"{hours:01d}ч {remaining_minutes:02d}мин"
                    else:
                        formatted_time = f"{hours:01d}ч"
                else:
                    formatted_time = f"{minutes}мин"
                if  botcalendar.calendar1.check_slot_availability(botcalendar.calen, master_name,  current_date_str, time_my, new_time_end):
                    buttons = types.InlineKeyboardButton(f"{service} {formatted_time} {price}₽", callback_data=f"{services}") 
                    markup.add(buttons)
        if user_info['datem']==False or user_info['masterm']==False:
            with open('dataservice.txt', 'r', encoding='utf-8') as file:
                services_data = file.readlines()              
            services = ''
            minutes = 0
            price = 0
            markup = types.InlineKeyboardMarkup(row_width=1)
            for line in services_data:
                service, minutes,price = line.strip().split(':')
                services=service.strip()
                services=services.replace("+", "")
                if int(minutes) >= 60:
                    hours = int(minutes) // 60
                    remaining_minutes = int(minutes) % 60
                    if remaining_minutes > 0:
                        formatted_time = f"{hours:01d}ч {remaining_minutes:02d}мин"
                    else:
                        formatted_time = f"{hours:01d}ч"
                else:
                    formatted_time = f"{minutes}мин"
                buttons = types.InlineKeyboardButton(f"{service} {formatted_time} ({price}₽)", callback_data=f"{services}")  
                markup.add(buttons) 
        bot.send_message(chat_id, text="Выберите действие ниже 👇", reply_markup=markup)

        
#выбрали услугу
    if callback.data in ['Стрижка', 'Детская стрижка', 'Стрижка машинкой', 'Укладка', 'Оформление бороды и усов', 'Оформление бороды', 'Стрижкаоформление бороды', 'Стрижка машинкойоформление бороды', 'Оформление усов','Стрижка (отец и сын)']:
        user_info['servicem'] = True
        chat_id = callback.message.chat.id
        markup = types.InlineKeyboardMarkup()
        data_to_write = ''
        service=callback.data
        with open('dataservice.txt', 'r', encoding='utf-8') as file:
         lines = file.readlines()
        for line in lines:
             if callback.data == line.split(':')[0].strip():  # Сравнение по названию услуги
                data_to_write = line.split(':')[1].strip()
        user_info['appointment_details']['service'] = service
        user_info['appointment_details']['time_service']=data_to_write
        bot.send_message(chat_id, f'Вы записались на: {callback.data}', reply_markup=markup)
        menu( chat_id,user_id )
 
#проверка данных

    if user_info['masterm'] == True and user_info['datem']==True and user_info['servicem'] ==True and (user_info['kx'] != 0):
        chat_id = callback.message.chat.id
        markup = types.InlineKeyboardMarkup()
        data_my = user_info['appointment_details']['data']
        current_date_str = data_my.strftime('%Y-%m-%d')
        month_day =current_date_str[5:]    
        time_my = user_info['appointment_details']['selected_time']          
        service_me = user_info['appointment_details']['service']      
        master_my = user_info['appointment_details']['master']
        message_text = f"Внимательно проверьте данные\n Дата: {month_day}\n Время: {time_my}\n Услуга: {service_me}\n Мастер: {master_my}\nВсе верно?\n"
        reply_markup = types.InlineKeyboardMarkup([[types.InlineKeyboardButton("Да", callback_data='yes'), types.InlineKeyboardButton("Нет", callback_data='no')]])  
        bot.send_message(chat_id, message_text, reply_markup=reply_markup)
        
        user_info['kx'] = 0 

    
    if callback.data == 'yes':
        if db.client_exists(int(user_info['appointment_details']['user_id'])) == False:
            msg = bot.send_message(chat_id, "Пожалуйста, напишите ваше имя и фамилию.")
            bot.register_next_step_handler(msg, process_name_step)
            
        else:
            selected_time = user_info['appointment_details']['selected_time']
            time_service_minutes = int(user_info['appointment_details']['time_service']) 
            time_format = "%H:%M"
            selected_time_dt = datetime.strptime(selected_time, time_format)
            time_service_delta = timedelta(minutes=time_service_minutes)
            new_time_dt = selected_time_dt + time_service_delta
            start_datetime = f"{selected_time_dt.strftime('%H:%M')}"
            end_datetime = f"{new_time_dt.strftime('%H:%M')}"
            
            name_client_know=db.get_client_name(int(user_info['appointment_details']['user_id']))
            if botcalendar.calendar1.is_slot_available(botcalendar.calen, user_info['appointment_details']['data'], start_datetime, end_datetime, user_info['appointment_details']['master']):
                 message_text = f"Извините, что-то пошло не так, возможно, на выбранное вами время уже кто-то записался, повторите попытку.Извините за неудобства🥺"
                 reply_markup = types.InlineKeyboardMarkup([[ types.InlineKeyboardButton("Повторить", callback_data='no')]])
                 bot.send_message(chat_id, message_text, reply_markup=reply_markup)
           
            else:
                master_id = db.get_master_id(user_info['appointment_details']['master'])
                botcalendar.calendar1.create_event(botcalendar.calen,name_client_know, user_info['appointment_details']['master'],user_info['appointment_details']['data'],user_info['appointment_details']['data'],start_datetime, end_datetime, names_to_numbers.get(user_info['appointment_details']['master']))
            
                db.add_service(int(user_info['appointment_details']['user_id']),master_id,user_info['appointment_details']['service'] ,str(user_info['appointment_details']['data']),str(user_info['appointment_details']['selected_time']))
                bot.send_message(chat_id, f'Вы успешно записаны. Мы вас ждем 😊\n\n Если вы хотите отменить запись, нажмите на кнопку *📍Профиль📍* ➡ *Мои заиписи* \n\n ❗ ⠀Важно⠀❗ \nОтменить запись можно только за 24 часа! ', reply_markup=types.InlineKeyboardMarkup(), parse_mode="Markdown")
    
    if callback.data == 'no':
        user_info['kx'] = 1
        markup = types.InlineKeyboardMarkup()
        btn21 = types.InlineKeyboardButton("Выбрать специалиста",callback_data='master')
        btn22 = types.InlineKeyboardButton("Выбрать дату и время",callback_data='date')
        btn23 = types.InlineKeyboardButton("Выбрать услугу",callback_data='service')

        markup.row(btn21)
        markup.row(btn22)
        markup.row(btn23)

        bot.send_message(
        chat_id, text=("Выберите дейтсвие ниже 👇"), reply_markup=markup)
        
    if callback.data =='confirm':
            
            selected_time = user_info['appointment_details']['selected_time']
            time_service_minutes = int(user_info['appointment_details']['time_service'])
            time_format = "%H:%M"
            selected_time_dt = datetime.strptime(selected_time, time_format)
            time_service_delta = timedelta(minutes=time_service_minutes)
            new_time_dt = selected_time_dt + time_service_delta
            start_datetime = f"{selected_time_dt.strftime('%H:%M')}"
            end_datetime = f"{new_time_dt.strftime('%H:%M')}"
            master_id = db.get_master_id(user_info['appointment_details']['master'])
            
            if botcalendar.calendar1.is_slot_available(botcalendar.calen, user_info['appointment_details']['data'], start_datetime, end_datetime, user_info['appointment_details']['master']):
                 message_text = f"Извините, что-то пошло не так, возможно, на выбранное вами время уже кто-то записался, повторите попытку.Извините за неудобства🥺"
                 reply_markup = types.InlineKeyboardMarkup([[ types.InlineKeyboardButton("Повторить", callback_data='no')]])
                 bot.send_message(chat_id, message_text, reply_markup=reply_markup)
           
            else:
                botcalendar.calendar1.create_event(botcalendar.calen,user_info['name_client'], user_info['appointment_details']['master'],user_info['appointment_details']['data'],user_info['appointment_details']['data'],start_datetime, end_datetime, names_to_numbers.get(user_info['appointment_details']['master']))
                db.add_client(int(user_info['appointment_details']['user_id']),user_info['name_client'],user_info['phone_client'],user_info['appointment_details']['user_nik'] )
                db.add_service(int(user_info['appointment_details']['user_id']),master_id,user_info['appointment_details']['service'] ,str(user_info['appointment_details']['data']),str(user_info['appointment_details']['selected_time']))
                bot.send_message(chat_id, f'Вы успешно записаны. Мы вас ждем 😊\n\n Если вы хотите отменить запись, нажмите на кнопку *📍Профиль📍* ➡ *Мои заиписи*   \n\n ❗ ⠀Важно⠀❗ \nОтменить запись можно только за 24 часа! ', reply_markup=types.InlineKeyboardMarkup(), parse_mode="Markdown")
         
    if callback.data == 'confirm_zapis':
        message_id = callback.message.message_id
        reply_markup = types.InlineKeyboardMarkup()
        bot.edit_message_text(chat_id=user_info['appointment_details']['user_id'], message_id=message_id, text=f"Запись подтверждена✅ ",reply_markup=reply_markup)
    if callback.data == 'cancel':
        message_id = callback.message.message_id
        reply_markup = types.InlineKeyboardMarkup([
                        [types.InlineKeyboardButton("Да", callback_data='cancel_zapis'), 
                         types.InlineKeyboardButton("Нет", callback_data='cancel_no')]
                    ])
        bot.edit_message_text(chat_id=user_info['appointment_details']['user_id'], message_id=message_id, text=f"Отменить запись?",reply_markup=reply_markup)
    if callback.data == 'cancel_no':
        message_id = callback.message.message_id
        reply_markup = types.InlineKeyboardMarkup([
                        [types.InlineKeyboardButton("Подтвердить", callback_data='confirm_zapis'), 
                         types.InlineKeyboardButton("Отменить запись", callback_data='cancel')]
                    ])
       
        bot.edit_message_text(chat_id=user_info['appointment_details']['user_id'], message_id=message_id, text=f"Подтверждаете запись?",reply_markup=reply_markup)

    if callback.data == 'cancel_zapis':
        reply_markup = types.InlineKeyboardMarkup()
        
        message_id = callback.message.message_id
        index=None
        if index is None:
            index = len(user_info['times']) - 1
        else:
            index = min(len(user_info['times']) - 1, max(0, index))
        timess=user_info['times'][index]
        db.delete_service_by_id(timess[2])
        description=db.get_master_name(timess[4])
        event_id=botcalendar.calendar1.get_events_id(botcalendar.calen, timess[0], timess[1], description)
        if botcalendar.calendar1.delete_event(botcalendar.calen, event_id):
           bot.edit_message_text(chat_id=callback.message.chat.id, message_id=message_id,text= "Запись отменена",reply_markup=reply_markup) 

def process_name_step(message):

    user_id = message.from_user.id
    user_info = get_user_data(user_id)
    user_info['name_client'] = message.text
    msg = bot.send_message(message.chat.id, "Пожалуйста, введите ваш номер телефона.")
    bot.register_next_step_handler(msg, process_phone_step)

def process_phone_step(message):
    user_id = message.from_user.id
    user_info = get_user_data(user_id)
    user_info['phone_client'] = message.text
    client_info_text = f"Имя и фамилия: {user_info['name_client']}\nНомер телефона: {user_info['phone_client']}\nВсе верно?"
    reply_markup = types.InlineKeyboardMarkup([[types.InlineKeyboardButton("Да", callback_data='confirm'), types.InlineKeyboardButton("Нет", callback_data='yes')]])
    bot.send_message(message.chat.id, client_info_text, reply_markup=reply_markup)

import time
def periodic_task(message):
    user_info = get_user_data(message)
    reply_markup = types.InlineKeyboardMarkup()
    index=None
    while True:
        client_id= user_info['appointment_details']['user_id']
        if client_id:
            new_times = db.get_appointments_24h_or_more(client_id)
            if new_times:
                if new_times != user_info['times']:
                    user_info['times'] = db.get_appointments_24h_or_more(client_id)
                    if index is None:
                        index = len(user_info['times']) - 1
                    else:
                        index = min(len(user_info['times']) - 1, max(0, index))
                    timess=user_info['times'][index]
                    full_date=timess[0]
                    short_date = full_date[5:]
                    reply_markup = types.InlineKeyboardMarkup([
                        [types.InlineKeyboardButton("Подтвердить", callback_data='confirm_zapis'), 
                         types.InlineKeyboardButton("Отменить запись", callback_data='cancel')]
                    ])
       
                    bot.send_message(chat_id=user_info['appointment_details']['user_id'], text=f"Здравствуйте! Напоминаем, что вы записаны к нам {short_date} в {timess[1]} на процедуру \"{timess[3]}\"",reply_markup=reply_markup)
        time.sleep(10)

def periodic_task_master(message):
    reply_markup = types.InlineKeyboardMarkup()
    cleints=[]
    index=None
    user_info = get_user_data(message)
    while True:
        if db.master_exists((int(message))):
                cleints = db.get_last_client_service(int(message))
                if cleints:
                    if cleints != user_info['new_client']:
                        user_info['new_client'] = db.get_last_client_service(int(message))

                        if index is None:
                            index = len(cleints) - 1
                            print (index)
                        else:
                            index = min(len(cleints) - 1, max(0, index))
                            print (index)
                        cleints[index]
                        
                        full_date=user_info['new_client'][1]
                        short_date = full_date[5:]
                        reply_markup = types.InlineKeyboardMarkup()
                        
                        bot.send_message(chat_id=message, text=f"У вас новая запись \nИмя: {cleints[0]} \nДата и время: {short_date}-{cleints[2]}\nУслуга: {cleints[3]}  ",reply_markup=reply_markup)
        time.sleep(10)

if __name__ == '__main__': 
    try:
        telegram.request.HTTPXRequest(proxy='http://127.0.0.1:3128')
        bot.polling(none_stop=True) 
    except Exception as e:
        print(e)