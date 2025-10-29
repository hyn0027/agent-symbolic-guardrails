import yaml
import os
from datetime import datetime
import logging


def get_logger(name: str, log_dir: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_filename = os.path.join(log_dir, f"{timestamp}.log")
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


class Config(dict):
    """A simple configuration class that extends dict."""

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(f"'Config' object has no attribute '{item}'")


def load_config(config_file: str) -> dict:
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    return Config(config)
