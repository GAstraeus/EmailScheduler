import json
import random
import time
import schedule
import os
import config.configuration as c
import helpers.emailClient as emailClient

def get_file_modified_time(filename):
    return os.path.getmtime(filename)

def random_time_in_range(start_time, end_time):
    start_hour, start_minute = map(int, start_time.split(":"))
    end_hour, end_minute = map(int, end_time.split(":"))
    random_hour = random.randint(start_hour, end_hour)
    random_minute = random.randint(start_minute if random_hour == start_hour else 0, end_minute if random_hour == end_hour else 59)
    return f"{random_hour:02}:{random_minute:02}"

def schedule_event(event):
    def task():
        emailClient.send_email(event[c.OWNER], json.dumps({c.EVENT_NAME: event[c.EVENT_NAME], c.MESSAGE: event[c.MESSAGE], c.RECIPIENT: event[c.RECIPIENT],}))


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


def start_event_scheduler():
    config_filename = "data/event_data.json"
    last_modified_time = get_file_modified_time(config_filename)

    with open(config_filename, c.R) as f:
        events = json.load(f)

    for event in events[c.EVENTS]:
        schedule_event(event)

    while True:
        current_modified_time = get_file_modified_time(config_filename)
        if current_modified_time != last_modified_time:
            print("Found new events in config")
            for event in events[c.EVENTS]:
                schedule.clear(event[c.EVENT_NAME])
            
            with open(config_filename, c.R) as f:
                events = json.load(f)
            
            for event in events[c.EVENTS]:
                schedule_event(event)

            last_modified_time = current_modified_time
        
        schedule.run_pending()
        time.sleep(1)
