# Modified from TAU2 bench code

from config_loader import CONFIG

dataset_config = CONFIG.DATASET

assert isinstance(
    dataset_config.AIRLINE_DB_PATH, str
), "AIRLINE_DB_PATH must be a string"
assert dataset_config.TMP_DB_PATH is None or isinstance(
    dataset_config.TMP_DB_PATH, str
), "TMP_DB_PATH must be a string or None"

AIRLINE_DB_PATH = dataset_config.AIRLINE_DB_PATH
TMP_DB_PATH = dataset_config.TMP_DB_PATH
