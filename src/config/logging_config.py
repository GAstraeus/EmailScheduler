import logging
import os
from datetime import datetime

logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))

# Create logs directory if it doesn't exist
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Set up logging configuration
log_filename = datetime.now().strftime(os.path.join(logs_dir, '%Y-%m-%d.log'))
logging.basicConfig(filename=log_filename, level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')