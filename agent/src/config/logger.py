import os
from datetime import datetime
import logging
from .loader import CONFIG


def setup_logger(name: str, log_path: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    log_filename = os.path.join(log_path, f"{timestamp}.log")
    file_handler = logging.FileHandler(log_filename, mode="a", encoding="utf-8")

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    console_handler.setLevel(logging.INFO)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


assert isinstance(CONFIG.SETTINGS.LOG_PATH, str), "Log path must be a string."

LOGGER = setup_logger("ReActAgent", CONFIG.SETTINGS.LOG_PATH)
