import yaml
from pathlib import Path
from typing import Optional, Union, Any
import argparse


class Config(dict):
    """A simple configuration class that extends dict."""

    def __getattr__(self, item) -> Union["Config", Any]:
        try:
            return Config(self[item]) if isinstance(self[item], dict) else self[item]
        except KeyError:
            return None


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from a YAML file."""
    if config_path is None:
        argparse_parser = argparse.ArgumentParser()
        argparse_parser.add_argument(
            "--config", type=str, default="config.yml", help="Path to the config file."
        )
        argparse_parser.add_argument(
            "--idx",
            type=str,
            default=None,
            help="Optional index to distinguish multiple runs.",
        )
        args, _ = argparse_parser.parse_known_args()
        config_path = Path(__file__).parent / args.config
    assert isinstance(config_path, (str, Path)), "config_path must be a string or Path"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    config = Config(config)
    if args.idx is not None:
        config["IDX"] = args.idx
    return config


CONFIG = load_config()
