from flask import Flask, request, jsonify, Response
from config.logging_config import logging
from emailScheduler import start_event_scheduler
import json
import threading
import re
import config.configuration as c

appConfig = c.Config(c.STAGE)

app = Flask(__name__)

@app.route('/addAbsoluteEvent', methods=['POST'])
def add_absolute_event():
    try:
        event = request.json
        if not all(k in event for k in ("name", "message", "owner", "time_setup")):
            return jsonify({"status": "error", "message": "Missing required fields!"}), 400
        
        time_setup = event["time_setup"]
        if not all(k in time_setup for k in ("days", "time")):
            return jsonify({"status": "error", "message": "Missing required time setup fields!"}), 400

        # Validate days
        valid_days = ["daily", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if not all(day in valid_days for day in time_setup["days"]):
            return jsonify({"status": "error", "message": "Invalid days provided!"}), 400
        
        # Validate time
        if not re.match(r"^(2[0-3]|[01]?[0-9]):([0-5]?[0-9])$", time_setup["time"]):
            return jsonify({"status": "error", "message": "Invalid time format!"}), 400
        
        # Append to config and save
        _save_to_config(event)
        return jsonify({"status": "success", "message": "Event added successfully!"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/addRangeEvent', methods=['POST'])
def add_range_event():
    _check_authorization(request)
    try:
        event = request.json
        if not all(k in event for k in ("name", "message", "owner", "time_setup")):
            return jsonify({"status": "error", "message": "Missing required fields!"}), 400
        
        time_setup = event["time_setup"]
        if not all(k in time_setup for k in ("days", "start", "end")):
            return jsonify({"status": "error", "message": "Missing required time setup fields!"}), 400

        # Validate days
        valid_days = ["daily", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if not all(day in valid_days for day in time_setup["days"]):
            return jsonify({"status": "error", "message": "Invalid days provided!"}), 400
        
        # Validate time
        time_pattern = r"^(2[0-3]|[01]?[0-9]):([0-5]?[0-9])$"
        if not (re.match(time_pattern, time_setup["start"]) and re.match(time_pattern, time_setup["end"])):
            return jsonify({"status": "error", "message": "Invalid time format!"}), 400
        
        # Ensure start time is earlier than end time
        start_time = [int(part) for part in time_setup["start"].split(":")]
        end_time = [int(part) for part in time_setup["end"].split(":")]
        if start_time >= end_time:
            return jsonify({"status": "error", "message": "Start time must be earlier than end time!"}), 400
        
        # Append to config and save
        _save_to_config(event)
        return jsonify({"status": "success", "message": "Event added successfully!"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route('/listEvents', methods=['GET'])
def list_events():
    _check_authorization(request)
    try:
        owner_email = request.args.get('owner')
        if not owner_email:
            return jsonify({"status": "error", "message": "Owner parameter is missing!"}), 400

        # Open the current config and find the events for the owner
        with open("data/config.json", "r") as f:
            config = json.load(f)

        # Filter events based on owner
        owner_events = [event for event in config["events"] if event["owner"] == owner_email]

        return jsonify({"status": "success", "events": owner_events}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def _save_to_config(event):
    with open("config.json", "r+") as f:
        config = json.load(f)
        config["events"].append(event)
        f.seek(0)
        json.dump(config, f, indent=4)
        f.truncate()

def _check_authorization(request):
     if not _validate_api_key(request):
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
     
def _validate_api_key(request):
    return request.headers.get('X-API-KEY') ==  appConfig.api_key

if __name__ == "__main__":
    scheduler_thread = threading.Thread(target=start_event_scheduler)
    scheduler_thread.start()
    app.run(port=5000, debug=True, use_reloader=False)

