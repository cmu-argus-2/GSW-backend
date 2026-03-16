import logging
import os
from datetime import datetime


_SESSION_TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
_LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
SESSION_LOG_FILE = os.path.join(_LOG_DIR, f"session_{_SESSION_TIMESTAMP}.log")


class _SessionLogFilter(logging.Filter):
    def __init__(self, session_id):
        super().__init__()
        self.session_id = session_id

    def filter(self, record):
        record.session_id = self.session_id
        return True


def get_session_logger(name):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.FileHandler(SESSION_LOG_FILE)
    formatter = logging.Formatter(
        "%(asctime)s | session=%(session_id)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(_SessionLogFilter(_SESSION_TIMESTAMP))

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
