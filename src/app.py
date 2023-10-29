from flask import Flask, request, jsonify, Response
from config.logging_config import logging
from emailScheduler import start_event_scheduler
import json
import threading
import re
import config.configuration as c

appConfig = c.Config(c.STAGE)

app = Flask(__name__)

@app.route('/addEvent', methods=['POST'])
def add_event():
    print(request)
    auth_error = _validate_authorization(request)
    print("api key validated")
    if auth_error:
        return auth_error
    try:
        event = request.json
        print(event)
        validation_error = _validate_event_from_request(event)

        if validation_error:
            return validation_error
        
        _save_to_config(event)
        return jsonify({"status": "success", "message": "Event added successfully!"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/listEvents', methods=['GET'])
def list_events():
    print(request)
    auth_error = _validate_authorization(request)
    if auth_error:
        return auth_error
    try:
        owner_email = request.args.get('owner')
        if not owner_email:
            return jsonify({"status": "error", "message": "Owner parameter is missing!"}), 400

        with open("data/event_data.json", "r") as f:
            config = json.load(f)

        owner_events = [event for event in config["events"] if event["owner"] == owner_email]

        return jsonify({"status": "success", "events": owner_events}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def _save_to_config(event):
    with open("data/event_data.json", "r+") as f:
        config = json.load(f)
        config["events"].append(event)
        f.seek(0)
        json.dump(config, f, indent=4)
        f.truncate()

def _validate_authorization(request):
     if not _validate_api_key(request):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
     return None
     
def _validate_api_key(request):
    return request.headers.get('X-API-KEY') ==  appConfig.api_key

def _validate_event_from_request(event: dict):
        valid_attributes = {"event_name", "message", "recipient", "owner", "time_setup"}

        if valid_attributes - set(event.keys()):
            return jsonify({"status": "error", "message": "Missing required fields!"}), 400
        
        if set(event.keys()) - valid_attributes:
            return jsonify({"status": "error", "message": "Passed in unknown fields"}), 400

        if not all(attribute in event for attribute in ("event_name", "message", "recipient", "owner", "time_setup")):
            return jsonify({"status": "error", "message": "Missing required fields!"}), 400
        
        if not event[c.EVENT_NAME]:
            return jsonify({"status": "error", "message": "Event name cannot be empty!"}), 400
        
        if not event[c.MESSAGE]:
            return jsonify({"status": "error", "message": "Message cannot be empty!"}), 400
        
        if not event[c.RECIPIENT]:
            return jsonify({"status": "error", "message": "Recipient field cannot be empty!"}), 400
        
        if not event[c.OWNER]:
            return jsonify({"status": "error", "message": "Owner field cannot be empty!"}), 400
        
        time_setup = event["time_setup"]
        
        if not all(time_attributes in time_setup for time_attributes in ("days", "type")):
            return jsonify({"status": "error", "message": "Missing required time setup fields!"}), 400
        
        if time_setup["type"] not in (c.ABSOLUTE, c.RANGE):
            return jsonify({"status": "error", "message": "time_setup type field not valid!"}), 400

        valid_days = ["daily", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if not all(day in valid_days for day in time_setup["days"]):
            return jsonify({"status": "error", "message": "Invalid days provided!"}), 400
        
        if time_setup[c.TYPE] == c.RANGE:
            if not time_setup[c.START]:
                return jsonify({"status": "error", "message": "No start time provided!"}), 400
            if not time_setup[c.END]:
                return jsonify({"status": "error", "message": "No start time provided!"}), 400

            if not (re.match(c.TIME_PATTERN, time_setup["start"]) and re.match(c.TIME_PATTERN, time_setup["end"])):
                return jsonify({"status": "error", "message": "Invalid time format!"}), 400
            
            start_time = [int(part) for part in time_setup["start"].split(":")]
            end_time = [int(part) for part in time_setup["end"].split(":")]
            if start_time >= end_time:
                return jsonify({"status": "error", "message": "Start time must be earlier than end time!"}), 400
            
        elif time_setup[c.TIME] == c.ABSOLUTE:
            if not time_setup[c.TIME]:
                return jsonify({"status": "error", "message": "No start time provided!"}), 400
        
            if not re.match(c.TIME_PATTERN, time_setup[c.TIME_PATTERN]):
                return jsonify({"status": "error", "message": "Invalid time format!"}), 400
        
        return None

if __name__ == "__main__":
    scheduler_thread = threading.Thread(target=start_event_scheduler)
    scheduler_thread.start()
    app.run(port=8123, debug=True, use_reloader=False)
