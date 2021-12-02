import logging

LOGGING_FORMAT = '%(levelname)s:%(name)s: %(message)s'

def make_logger(name: str, level=logging.INFO) -> logging.Logger:
    """Return a dedicated logger for a module."""
    log = logging.getLogger(name)
    log.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
    log.addHandler(handler)
    return log