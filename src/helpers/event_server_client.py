import requests
import sys

running_via_gunicorn = 'gunicorn' in sys.argv[0] or 'gunicorn' in sys.modules

if running_via_gunicorn:
    import src.config.configuration as c
    import src.helpers.emailClient as emailClient
    from src.config.logging_config import logging
else:
    import config.configuration as c
    import helpers.emailClient as emailClient
    from config.logging_config import logging

appConfig = c.Config(c.STAGE)

deleteEndpoint = "/deleteEvent"

def deleteEvent(eventId):
    logging.info(f"Deleting eventId: {eventId}")
    headers = {
        c.X_API_KEY : appConfig.api_key
    }
    params = {
        c.ID : eventId
    }
    response = requests.delete(appConfig.url+deleteEndpoint, headers=headers, params=params)

    if response.status_code == 200:
        logging.info(f"Successfully deleted eventId: {eventId}")
    else:
        logging.info(f"Failed to delete eventId: {eventId}")
