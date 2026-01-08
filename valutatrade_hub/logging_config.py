# valutatrade_hub/logging_config.py

import logging
import os
from logging.handlers import RotatingFileHandler

from .infra.settings import settings


def setup_logging():
    '''
    Функция для реализации логирования
    '''
    log_file = settings.get('log_file', 'logs/valutatrade.log')
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger("valutatrade")
    logger.setLevel(settings.get('log_level', 'INFO'))

    handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5)
    formatter = logging.Formatter('%(levelname)s %(asctime)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
    handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

app_logger = setup_logging()