# Modified from TAU2 bench code

from config_loader import CONFIG
from pathlib import Path

dataset_config = CONFIG.DATASET

AIRLINE_DATA_DIR = Path(dataset_config.DOMAIN_PATH) / dataset_config.DOMAIN
AIRLINE_DB_PATH = AIRLINE_DATA_DIR / "db.json"
AIRLINE_POLICY_PATH = AIRLINE_DATA_DIR / "policy.md"
AIRLINE_TASK_SET_PATH = AIRLINE_DATA_DIR / "tasks.json"
