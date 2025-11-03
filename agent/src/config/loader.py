import yaml
from pathlib import Path
from typing import Optional


class Config(dict):
    """A simple configuration class that extends dict."""

    def __getattr__(self, item):
        try:
            return Config(self[item]) if isinstance(self[item], dict) else self[item]
        except KeyError:
            raise AttributeError(f"'Config' object has no attribute '{item}'")


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from a YAML file."""
    if config_path is None:
        config_path = Path(__file__).parent / "config.yml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return Config(config)


CONFIG = load_config()
