import configparser
from src.config.logging_config import logging
import os

class Config:
    _instance = None
    _is_init = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, env):
        if self._is_init:
            return
        config = configparser.ConfigParser()
        current_dir = os.path.abspath(os.path.dirname(__file__))
        config_path = os.path.join(current_dir, 'config.ini')
        config.read(config_path)
        self.smtp_server = config[env]['smtp_server']
        self.smtp_port = config[env]['smtp_port']
        self.smtp_user = config[env]['email']
        self.password = config[env]['password']
        self.api_key = config[env]['api_key']
        self._is_init = True


PROD_STAGE = 'Prod'
DEV_STAGE = 'Dev'
STAGE = PROD_STAGE

ABSOLUTE = "absolute"
COLON = ":"
DAILY = "daily"
DAYS = "days"
EMAIL = "email"
EMAIL_SETTINGS = "email_settings"
END = "end"
ERROR = "error"
EVENT_NAME = "event_name"
EVENTS = "events"
FROM = 'From'
GET = "GET"
MESSAGE = "message"
NAME = "name"
OWNER = "owner"
PASSWORD = "password"
POST = "POST"
R = "r"
R_PLUS = "r+"
RANGE = "range"
RECIPIENT = "recipient"
SMTP_PORT = "smtp_port"
SMTP_SERVER = "smtp_server"
START = "start"
STATUS = "status"
SUBJECT = 'Subject'
SUCCESS = "success"
TIME = "time"
TIME_PATTERN = r"^(2[0-3]|[01]?[0-9]):([0-5]?[0-9])$"
TIME_SETUP = "time_setup"
TO = 'To'
TYPE = "type"

# DAYS 
DAILY = "daily"
MONDAY = "Monday"
TUESDAY = "Tuesday"
WEDNESDAY = "Wednesday"
THURSDAY = "Thursday"
FRIDAY = "Friday"
SATURDAY = "Saturday"
SUNDAY = "Sunday"

EVENTS_DATA_FILE_NAME = "event_data.json"
current_dir = os.path.dirname(os.path.abspath(__file__))
EVENTS_DATA_FILE_PATH = os.path.join(current_dir, '..', 'data', EVENTS_DATA_FILE_NAME)

logging.debug(f"Using Environment Stage {STAGE}")