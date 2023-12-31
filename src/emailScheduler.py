import json
import random
import time
import schedule
import os
import sys
import datetime

running_via_gunicorn = 'gunicorn' in sys.argv[0] or 'gunicorn' in sys.modules

if running_via_gunicorn:
    import src.config.configuration as c
    import src.helpers.emailClient as emailClient
    import src.helpers.event_server_client as serviceClient
    from src.config.logging_config import logging
else:
    import config.configuration as c
    import helpers.emailClient as emailClient
    import helpers.event_server_client as serviceClient
    from config.logging_config import logging


def get_file_modified_time(filename):
    return os.path.getmtime(filename)

def random_time_in_range(start_time, end_time):
    start_hour, start_minute = map(int, start_time.split(c.COLON))
    end_hour, end_minute = map(int, end_time.split(c.COLON))
    random_hour = random.randint(start_hour, end_hour)
    random_minute = random.randint(start_minute if random_hour == start_hour else 0, end_minute if random_hour == end_hour else 59)
    return f"{random_hour:02}:{random_minute:02}"

def schedule_event(event):
    def task():
        emailClient.send_email(event[c.OWNER], json.dumps({c.EVENT_NAME: event[c.EVENT_NAME], c.MESSAGE: event[c.MESSAGE], c.RECIPIENT: event[c.RECIPIENT],}))
        if event[c.TIME_SETUP][c.TYPE] == c.DATE:
            serviceClient.deleteEvent(event[c.ID])


    if event[c.TIME_SETUP][c.TYPE] == c.ABSOLUTE:
        for day in event[c.TIME_SETUP][c.DAYS]:
            if day.lower() == c.DAILY:
                schedule.every().day.at(event[c.TIME_SETUP][c.TIME]).do(task)
            else:
                getattr(schedule.every(), day.lower()).at(event[c.TIME_SETUP][c.TIME]).do(task)
    elif event[c.TIME_SETUP][c.TYPE] == c.RANGE:
        for day in event[c.TIME_SETUP][c.DAYS]:
            random_time = random_time_in_range(event[c.TIME_SETUP][c.START], event[c.TIME_SETUP][c.END])
            if day.lower() == c.DAILY:
                schedule.every().day.at(random_time).do(task)
            else:
                getattr(schedule.every(), day.lower()).at(random_time).do(task)
    elif event[c.TIME_SETUP][c.TYPE] == c.DATE:
        event_date = datetime.datetime.strptime(event[c.TIME_SETUP][c.DAYS][0], '%Y-%m-%d').date()
        today = datetime.datetime.today().date()
        if event_date == today:
            schedule.every().day.at(event[c.TIME_SETUP][c.TIME]).do(task).tag('once')
            

def is_reschedule_time():
    now = datetime.datetime.now()
    return now.hour == 2 and now.minute == 2


def start_event_scheduler():
    last_modified_time = get_file_modified_time(c.EVENTS_DATA_FILE_PATH)

    with open(c.EVENTS_DATA_FILE_PATH, c.R) as f:
        events = json.load(f)

    for event in events[c.EVENTS]:
        schedule_event(event)

    while True:
        current_modified_time = get_file_modified_time(c.EVENTS_DATA_FILE_PATH)
        if current_modified_time != last_modified_time or is_reschedule_time():
            logging.info("Found new events in config")
            schedule.clear()
            
            with open(c.EVENTS_DATA_FILE_PATH, c.R) as f:
                events = json.load(f)
            
            logging.info(f"Scheduling {len(events[c.EVENTS])} events")
            for event in events[c.EVENTS]:
                schedule_event(event)

            last_modified_time = current_modified_time
        
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    start_event_scheduler()