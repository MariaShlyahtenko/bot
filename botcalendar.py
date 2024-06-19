#from distutils.command.build import build
import telebot
from datetime import datetime, timezone, timedelta
import calendar
from telebot import types
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetimerange import DateTimeRange
from dateutil.relativedelta import relativedelta
import pytz
all_target_descriptions = ['Оксана Самойлова', 'Дмитрий Васильков', 'Алексей Бочкарев', 'Алексей Вавилов', 'Мария Гончарова']
MONTHS_RU = {
    'January': 'Январь',
    'February': 'Февраль',
    'March': 'Март',
    'April': 'Апрель',
    'May': 'Май',
    'June': 'Июнь',
    'July': 'Июль',
    'August': 'Август',
    'September': 'Сентябрь',
    'October': 'Октябрь',
    'November': 'Ноябрь',
    'December': 'Декабрь'
}

class GoogleCalendar:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    FILE_PATH = 'jsbot1.json'

    def __init__(self):
        credentialss = service_account.Credentials.from_service_account_file(
            filename=self.FILE_PATH, scopes=self.SCOPES
        )
        self.service = build('calendar', 'v3', credentials=credentialss)

    def get_calendar_list(self):
        return self.service.calendarList().list().execute()

    def add_calendar(self, calendar_id):
        calendar_list_entry = {
            'id': calendar_id
        }

        return self.service.calendarList().insert(body=calendar_list_entry).execute()

    def add_event(self, calendar_id, body):
        return self.service.events().insert(
            calendarId=calendar_id,
            body=body).execute()
    
    def get_current_month_name(self):
        now = datetime.now()
        english_month_name = now.strftime("%B")
        russian_month_name = MONTHS_RU.get(english_month_name)

        return russian_month_name

    def get_next_month(self):
        now = datetime.now()
        next_month = now.replace(month=now.month % 12 + 1)
        return MONTHS_RU.get(next_month.strftime("%B"))
    
    def get_free_time_slots(self, calendar_id, all_target_descriptions, target_date, user_info,time_service):

        target_date = datetime.strptime(target_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        free_slots = []    
        busy_slots = set()
        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=target_date.isoformat(),
            timeMax=(target_date + timedelta(days=1)).isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        data_to_write = 0 
        events = events_result.get('items', [])
        if user_info['servicem']==True: 
            if time_service != '': 
                try:
                    data_to_write = int(time_service)
                    print(data_to_write)
                except ValueError:
                    print("Unable to convert to an integer:", data_to_write)
                else:
                    print("Empty value for service time")
        print(data_to_write)
        master_slots = []
        if user_info['masterm'] ==False or user_info['masterm'] ==True:
            all_free_slots = set()
            for member in all_target_descriptions:
                busy_slots = set()
                for event in events_result.get("items", []):
                    start = event.get("start", {}).get("dateTime")
                    end = event.get("end", {}).get("dateTime")
                    description = event.get("description")
                    if start and end and (not description or member in description):
                        event_start = datetime.fromisoformat(start)
                        event_start -= timedelta(minutes=int(data_to_write))
                        while event_start < datetime.fromisoformat(end):
                            busy_slots.add(event_start.replace(tzinfo=timezone.utc).isoformat())
                            event_start += timedelta(minutes=1)
                member_free_slots = set()
                for hour in range(11, 22):
                    slot_start = target_date.replace(hour=hour, minute=0, second=0)
                    slot_end = slot_start + timedelta(hours=1)
                    if int(slot_end.hour)<22:
                        if not any(slot_start <= datetime.fromisoformat(busy_slot) < slot_end for busy_slot in busy_slots):
                            member_free_slots.add(slot_start.strftime("%H:%M"))
                all_free_slots.update(member_free_slots)
            free_slots = sorted(list(all_free_slots))
        if free_slots:
            return free_slots
        else:
            return None

    # Список всех мастеров

    def check_slot_availability(self, calendar_id, all_target_descriptions, target_date, chekstart_time, end_time):
        target_date = datetime.strptime(target_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        busy_slots = set()

        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=target_date.isoformat(),
            timeMax=(target_date + timedelta(days=1)).isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        data_to_write = 0  
        events = events_result.get('items', [])
        for event in events:
            start = event.get('start', {}).get('dateTime')
            
            end = event.get('end', {}).get('dateTime')
            description = event.get('description')
            
            if start and end and (not all_target_descriptions or description in all_target_descriptions):
                event_start = datetime.fromisoformat(start)
                
                event_start -= timedelta(minutes=int(data_to_write))
                while event_start < datetime.fromisoformat(end):
                    busy_slots.add(event_start.replace(tzinfo=timezone.utc).isoformat())
                    
                    event_start += timedelta(minutes=1)
        slot_range = DateTimeRange(chekstart_time, end_time)

        for busy_slot in busy_slots:
            busy_start = datetime.fromisoformat(busy_slot).replace(tzinfo=None)
            busy_end = busy_start + timedelta(minutes=1)

            if slot_range.is_intersection(DateTimeRange(busy_start, busy_end)):
                return False 

        return True
    

    def get_busy_descriptions(self, calendar_id, target_datetime,end_date):
        busy_descriptions = []
        tz = pytz.timezone('Etc/GMT-7')
        target_date = datetime.fromisoformat(target_datetime).replace(tzinfo=tz)
        end_dat=datetime.fromisoformat(end_date).replace(tzinfo=tz)
        print("Target Date:", target_date)
        
        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=target_date.isoformat(),
            timeMax=end_dat.isoformat(),  # Проверяем только одну минуту
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        for event in events:
            description = event.get('description')
            if description:
                busy_descriptions.append(description)
        
        return busy_descriptions
    def create_event(self,calendar_id,summary, description,date,end_date, start_datetime, end_datetime, color_id):
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': f'{date}T{start_datetime}:00+07:00',
            },
            'end': {
                'dateTime': f'{end_date}T{end_datetime}:00+07:00',
            },
            'colorId': color_id
        }
        self.add_event(calendar_id, body=event)
        return event
    def get_events_id(self, calendar_id, date, start_datetime, description):
        start_time_dt = datetime.strptime(start_datetime, "%H:%M")
            
            # Добавляем одну минуту
        end_time_dt = start_time_dt + timedelta(minutes=1)
            
            # Преобразуем обратно в строку в формате HH:MM
        end_datetime_str = end_time_dt.strftime("%H:%M")
        try:
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=f'{date}T{start_datetime}:00+07:00',
                timeMax=f'{date}T{end_datetime_str}:00+07:00',
                singleEvents=True,
                orderBy='startTime'
                
            ).execute()
            event= events_result.get('items', [])
            if event:
                for events in event:
                    events_result_descript = events.get('description')
                    if events_result_descript  == description:
                        return events.get('id')
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
    def get_events(self, calendar_id, date,end_date, start_datetime, end_datetime):
        try:
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=f'{date}T{start_datetime}:00+07:00',
                timeMax=f'{end_date}T{end_datetime}:00+07:00',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
    def delete_event(self, calendar_id, event_id):
        try:
            self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            print("Event deleted successfully")
            return True
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
    def is_slot_available(self, calendar_id, date, start_datetime, end_datetime, description):
            events = self.get_events(
                calendar_id,
                date,
                date,
                start_datetime,
                end_datetime
            )

            if not events:
                return False

            slot_range = DateTimeRange(
                f"{date}T{start_datetime}:00+07:00",
                f"{date}T{end_datetime}:00+07:00"
            )

            for event in events:
                event_start = event['start'].get('dateTime')
                event_end = event['end'].get('dateTime')
                event_description = event.get('description')

                if event_start and event_end and event_description == description:
                    event_range = DateTimeRange(event_start, event_end)
                    print (event_range)
                    print(slot_range)
                    if slot_range.is_intersection(event_range):
                        return True

            return False
    def is_event_within_24_hours(self, calendar_id, date, start_datetime, description):
        now = datetime.now(pytz.timezone('Etc/GMT-7'))  # Используйте правильный часовой пояс
        end_date = date  # Мы ищем события только на одну дату
        start_time_dt = datetime.strptime(start_datetime, "%H:%M")
            
            # Добавляем одну минуту
        end_time_dt = start_time_dt + timedelta(minutes=1)
            
            # Преобразуем обратно в строку в формате HH:MM
        end_datetime_str = end_time_dt.strftime("%H:%M")
        print (end_datetime_str)
        events = self.get_events(calendar_id, date,end_date, start_datetime, end_datetime_str)
        if not events:
            return False

        for event in events:
            event_start = event['start'].get('dateTime')
            event_description = event.get('description')

            if event_start and event_description == description:
                event_start_datetime = datetime.fromisoformat(event_start).astimezone(pytz.timezone('Etc/GMT-7'))
                time_difference = event_start_datetime - now
                if time_difference >= timedelta(hours=24):
                    return True

        return False
    def chek_24_hours(self, calendar_id, date, start_datetime, description):
        now = datetime.now(pytz.timezone('Etc/GMT-7'))  # Используйте правильный часовой пояс
        end_date = date  # Мы ищем события только на одну дату
        start_time_dt = datetime.strptime(start_datetime, "%H:%M")
            
            # Добавляем одну минуту
        end_time_dt = start_time_dt + timedelta(minutes=1)
            
            # Преобразуем обратно в строку в формате HH:MM
        end_datetime_str = end_time_dt.strftime("%H:%M")
        print (end_datetime_str)
        events = self.get_events(calendar_id, date,end_date, start_datetime, end_datetime_str)
        if not events:
            return False

        for event in events:
            event_start = event['start'].get('dateTime')
            event_description = event.get('description')

            if event_start and event_description == description:
                event_start_datetime = datetime.fromisoformat(event_start).astimezone(pytz.timezone('Etc/GMT-7'))
                time_difference = event_start_datetime - now
                if time_difference == timedelta(hours=24):
                    return True

        return False

        

calendar1 = GoogleCalendar()
calen = 'ms.shlyahtenko@gmail.com'



