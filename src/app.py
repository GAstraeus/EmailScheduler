from flask import Flask, request, jsonify, Response
from src.config.logging_config import logging
from src.emailScheduler import start_event_scheduler
from datetime import datetime
import json
import threading
import re
import hashlib
import src.config.configuration as c

appConfig = c.Config(c.STAGE)

app = Flask(__name__)

@app.route('/addEvent', methods=[c.POST])
def add_event():
    auth_error = _validate_authorization(request)
    if auth_error:
        return auth_error
    try:
        event = request.json
        validation_error = _validate_event_from_request(event)

        if validation_error:
            return validation_error
        
        event[c.ID] = _generate_event_hash(event)

        _add_event_to_events_datafile(event)
        return jsonify({c.STATUS: c.SUCCESS, c.MESSAGE: "Event added successfully!"}), 200

    except Exception as e:
        return jsonify({c.STATUS: c.ERROR, c.MESSAGE: str(e)}), 500

@app.route('/listEvents', methods=[c.GET])
def list_events():
    auth_error = _validate_authorization(request)
    if auth_error:
        return auth_error
    try:
        owner_email = request.args.get('owner')
        if not owner_email:
            return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Owner parameter is missing!"}), 400
        
        events = _read_datafile()

        owner_events = [event for event in events[c.EVENTS] if event[c.OWNER] == owner_email]

        return jsonify({c.STATUS: c.SUCCESS, c.EVENTS: owner_events}), 200

    except Exception as e:
        return jsonify({c.STATUS: c.ERROR, c.MESSAGE: str(e)}), 500

@app.route('/deleteEvent', methods=[c.DELETE])
def delete_event():
    auth_error = _validate_authorization(request)
    if auth_error:
        return auth_error
    event_id = request.args.get(c.ID)
    if not event_id:
        return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Event ID is required!"}), 400
    _remove_event_from_events_datafile(event_id)
    return jsonify({c.STATUS: c.SUCCESS, c.MESSAGE: "Event deleted successfully!"}), 200

def _read_datafile():
    with open(c.EVENTS_DATA_FILE_PATH, c.R) as f:
        return json.load(f)

def _write_datafile(events):
    with open(c.EVENTS_DATA_FILE_PATH, c.W) as f:
        json.dump(events, f, indent=4)

def _add_event_to_events_datafile(event):
    events = _read_datafile()
    events[c.EVENTS].append(event)
    _write_datafile(events)

def _remove_event_from_events_datafile(event_id):
    events = _read_datafile()
    events[c.EVENTS] = [event for event in events[c.EVENTS] if event.get(c.ID) != event_id]
    _write_datafile(events)

def _validate_authorization(request):
     if not _validate_api_key(request):
        return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Unauthorized"}), 401
     return None
     
def _validate_api_key(request):
    return request.headers.get(c.X_API_KEY) ==  appConfig.api_key

def _validate_event_from_request(event: dict):
        valid_attributes = {c.EVENT_NAME, c.MESSAGE, c.RECIPIENT, c.OWNER, c.TIME_SETUP}

        if valid_attributes - set(event.keys()):
            return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Missing required fields!"}), 400
        
        if set(event.keys()) - valid_attributes:
            return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Passed in unknown fields"}), 400
        
        if not event[c.EVENT_NAME]:
            return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Event name cannot be empty!"}), 400
        
        if not event[c.MESSAGE]:
            return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Message cannot be empty!"}), 400
        
        if not event[c.RECIPIENT]:
            return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Recipient field cannot be empty!"}), 400
        
        if not event[c.OWNER]:
            return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Owner field cannot be empty!"}), 400
        
        time_setup = event[c.TIME_SETUP]
        
        if not all(time_attributes in time_setup for time_attributes in ("days", "type")):
            return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Missing required time setup fields!"}), 400
        
        if time_setup[c.TYPE] not in (c.ABSOLUTE, c.RANGE, c.DATE):
            return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "time_setup type field not valid!"}), 400
        

        if time_setup[c.TYPE] == c.ABSOLUTE or time_setup[c.TYPE] == c.RANGE:
            valid_days = [c.DAILY, c.MONDAY, c.TUESDAY, c.WEDNESDAY, c.THURSDAY, c.FRIDAY, c.SATURDAY, c.SUNDAY]
            if not all(day in valid_days for day in time_setup[c.DAYS]):
                return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Invalid days provided!"}), 400
        elif time_setup[c.TYPE] == c.DATE:
            if len(time_setup[c.DAYS]) > 1:
                return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Only one date allowed!"}), 400
            try:
                input_date = datetime.strptime(time_setup[c.DAYS][0], '%Y-%m-%d').date()
                today = datetime.today().date()
                if input_date < today:
                    return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Date should not be in the past!"}), 400
            except ValueError:
                return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Date should have format %Y-%m-%d!"}), 400

        if time_setup[c.TYPE] == c.RANGE:
            if not time_setup[c.START]:
                return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "No start time provided!"}), 400
            if not time_setup[c.END]:
                return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "No start time provided!"}), 400

            if not (re.match(c.TIME_PATTERN, time_setup[c.START]) and re.match(c.TIME_PATTERN, time_setup[c.END])):
                return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Invalid time format!"}), 400
            
            start_time = [int(part) for part in time_setup[c.START].split(c.COLON)]
            end_time = [int(part) for part in time_setup[c.END].split(c.COLON)]
            if start_time >= end_time:
                return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Start time must be earlier than end time!"}), 400
            
        elif time_setup[c.TYPE] == c.ABSOLUTE or time_setup[c.TYPE] == c.DATE:
            if not time_setup[c.TIME]:
                return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "No start time provided!"}), 400
        
            if not re.match(c.TIME_PATTERN, time_setup[c.TIME]):
                return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Invalid time format!"}), 400
        
        return None

def _generate_event_hash(event: dict):
    md5_hash = hashlib.md5()
    event_string = str(event)+str(datetime.now)
    md5_hash.update(event_string.encode('utf-8'))
    hex_dig_hash = md5_hash.hexdigest()
    return hex_dig_hash

if __name__ == "__main__":
    scheduler_thread = threading.Thread(target=start_event_scheduler)
    scheduler_thread.start()
    app.run(port=8123, debug=False, use_reloader=False)
