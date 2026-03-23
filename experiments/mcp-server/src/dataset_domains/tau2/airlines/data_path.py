# Modified from TAU2 bench code

from config_loader import CONFIG

dataset_config = CONFIG.DATASET

assert isinstance(
    dataset_config.AIRLINE_DB_PATH, str
), "AIRLINE_DB_PATH must be a string"

AIRLINE_DB_PATH = dataset_config.AIRLINE_DB_PATH
