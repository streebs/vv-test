import logging
from logging.handlers import RotatingFileHandler


def create_logger(logfile, size, backup, minlevel):
    logger = logging.getLogger("Rotating Log")
    if minlevel == "debug":
        logger.setLevel(logging.DEBUG)
    elif minlevel == "info":
        logger.setLevel(logging.INFO)
    elif minlevel == "warning":
        logger.setLevel(logging.WARNING)
    elif minlevel == "error":
        logger.setLevel(logging.ERROR)
    elif minlevel == "critical":
        logger.setLevel(logging.CRITICAL)
    # Setup size of log files and the num of backups: 2mb current and 1 backup
    handler = RotatingFileHandler(logfile, maxBytes=size, backupCount=backup)
    logger.addHandler(handler)
    # Log lines will look like the following. Time - Level(Debug,etc) - Message
    formatter = logging.Formatter('%(asctime)s - %(levelname)s -%(message)s')
    handler.setFormatter(formatter)
    return logger
