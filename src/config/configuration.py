import configparser
from config.logging_config import logging
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
FROM = 'From'
SUBJECT = 'Subject'
TO = 'To'
OWNER = "owner"
EVENT_NAME = "event_name"
MESSAGE = "message"
RECIPIENT = "recipient"
SMTP_SERVER = "smtp_server"
SMTP_PORT = "smtp_port"
EMAIL = "email"
PASSWORD = "password"
ABSOLUTE = "absolute"
DAILY = "daily"
DAYS = "days"
EMAIL_SETTINGS = "email_settings"
END = "end"
EVENTS = "events"
NAME = "name"
R = "r"
RANGE = "range"
START = "start"
TIME = "time"
TIME_SETUP = "time_setup"
TYPE = "type"
TIME_PATTERN = r"^(2[0-3]|[01]?[0-9]):([0-5]?[0-9])$"

logging.debug(f"Using Environment Stage {STAGE}")