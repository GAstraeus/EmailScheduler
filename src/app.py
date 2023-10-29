from flask import Flask, request, jsonify, Response
from src.config.logging_config import logging
from src.emailScheduler import start_event_scheduler
import json
import threading
import re
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
        
        _save_to_config(event)
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

        with open(c.EVENTS_DATA_FILE_PATH, c.R) as f:
            config = json.load(f)

        owner_events = [event for event in config[c.EVENTS] if event[c.OWNER] == owner_email]

        return jsonify({c.STATUS: c.SUCCESS, c.EVENTS: owner_events}), 200

    except Exception as e:
        return jsonify({c.STATUS: c.ERROR, c.MESSAGE: str(e)}), 500

def _save_to_config(event):
    with open(c.EVENTS_DATA_FILE_PATH, c.R_PLUS) as f:
        config = json.load(f)
        config[c.EVENTS].append(event)
        f.seek(0)
        json.dump(config, f, indent=4)
        f.truncate()

def _validate_authorization(request):
     if not _validate_api_key(request):
        return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Unauthorized"}), 401
     return None
     
def _validate_api_key(request):
    return request.headers.get('X-API-KEY') ==  appConfig.api_key

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
        
        if time_setup[c.TYPE] not in (c.ABSOLUTE, c.RANGE):
            return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "time_setup type field not valid!"}), 400

        valid_days = [c.DAILY, c.MONDAY, c.TUESDAY, c.WEDNESDAY, c.THURSDAY, c.FRIDAY, c.SATURDAY, c.SUNDAY]
        if not all(day in valid_days for day in time_setup[c.DAYS]):
            return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Invalid days provided!"}), 400
        
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
            
        elif time_setup[c.TIME] == c.ABSOLUTE:
            if not time_setup[c.TIME]:
                return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "No start time provided!"}), 400
        
            if not re.match(c.TIME_PATTERN, time_setup[c.TIME_PATTERN]):
                return jsonify({c.STATUS: c.ERROR, c.MESSAGE: "Invalid time format!"}), 400
        
        return None

if __name__ == "__main__":
    scheduler_thread = threading.Thread(target=start_event_scheduler)
    scheduler_thread.start()
    app.run(port=8123, debug=False, use_reloader=False)
