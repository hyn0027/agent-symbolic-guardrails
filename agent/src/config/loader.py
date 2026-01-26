import yaml
import argparse
from pathlib import Path
from typing import Optional, Union, Any


class Config(dict):
    """A simple configuration class that extends dict."""

    def __getattr__(self, item) -> Union["Config", Any]:
        try:
            return Config(self[item]) if isinstance(self[item], dict) else self[item]
        except KeyError:
            raise AttributeError(f"'Config' object has no attribute '{item}'")


def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """Load configuration from a YAML file."""
    if config_path is None:
        config_path = Path(__file__).parent / "config.yml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return Config(config)


parser = argparse.ArgumentParser()
parser.add_argument(
    "--config",
    type=str,
    default=None,
    help="Path to config file (YAML)",
)
parser.add_argument(
    "-id", "--task_id", type=int, required=False, help="ID of the task to run."
)
args = parser.parse_args()
CONFIG = load_config(args.config)

