# Modified from TAU2 bench code

from config_loader import CONFIG
from pathlib import Path

dataset_config = CONFIG.DATASET


AIRLINE_DB_PATH = dataset_config.AIRLINE_DB_PATH
TMP_DB_PATH = dataset_config.TMP_DB_PATH