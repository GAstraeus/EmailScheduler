import smtplib
import sys
from email.mime.text import MIMEText

running_via_gunicorn = 'gunicorn' in sys.argv[0] or 'gunicorn' in sys.modules

if running_via_gunicorn:
    import src.config.configuration as c
    from src.config.logging_config import logging
else:
    import config.configuration as c
    from config.logging_config import logging

appConfig = c.Config(c.STAGE)

def send_email(to, body):
    msg = MIMEText(body)
    msg[c.FROM] = appConfig.smtp_user
    msg[c.TO] = to

    logging.info(f"Sending email to {to}...")

    server = smtplib.SMTP(appConfig.smtp_server, appConfig.smtp_port)
    server.starttls()
    server.login(appConfig.smtp_user, appConfig.password)
    server.sendmail(appConfig.smtp_user, to, msg.as_string())
    server.quit()