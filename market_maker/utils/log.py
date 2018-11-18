import logging, time
from market_maker.settings import settings



def setup_custom_logger(name, log_level=settings.LOG_LEVEL):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    logging.Formatter.converter = time.gmtime # we want to use UTC time, to keep consistency across platforms and timezones

    handler = logging.StreamHandler() # sends logging output to streams such as sys.stdout, sys.stderr or any file-like object
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.addHandler(handler)
    return logger
