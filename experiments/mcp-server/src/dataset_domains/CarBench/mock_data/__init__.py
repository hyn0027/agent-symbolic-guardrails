import os
import sys
import traceback

from dataset_domains.CarBench.context.dynamic_context_state import (
    ContextState,
)
from dataset_domains.CarBench.context.fixed_context import FixedContext

from .data_manager import DataManager
import contextlib, io, os

# Define lists (you can choose one list or separate ones)
ALL_STATE_MODELS = [ContextState]

ALL_CONTEXT_MODELS = [FixedContext]

ALL_MODELS = ALL_STATE_MODELS + ALL_CONTEXT_MODELS


def _resolve_data_directory() -> str:
    """Download mock data JSONL files from HuggingFace and return the cached path."""
    from huggingface_hub import snapshot_download
    from huggingface_hub.utils import disable_progress_bars
    from huggingface_hub import logging as hf_logging

    repo_id = "johanneskirmayr/car-bench-dataset"

    disable_progress_bars()
    hf_logging.set_verbosity_error()

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
        io.StringIO()
    ):
        local_dir = snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            allow_patterns=["mock_data/**"],
        )

    data_path = os.path.join(local_dir, "mock_data")
    return data_path


class _LazyDataManager:
    """Lazy proxy that defers DataManager creation until first attribute access.

    This is necessary because mock_data/__init__.py is imported at module load
    time (triggered by run.py's top-level imports), but the CLI args that
    control the HF repo ID are only parsed later in main().  By deferring
    initialization, we ensure the env vars are read at the right time.

    Call ``initialize()`` explicitly before running tasks to pre-load all
    mock data so every task has the same runtime characteristics.
    """

    def __init__(self):
        self._instance = None

    def initialize(self):
        """Eagerly create the DataManager (downloads from HF + preloads data).

        Safe to call multiple times — only the first call does real work.
        """
        self._get_instance()

    def _get_instance(self):
        if self._instance is None:
            # print("Initializing shared Car VA DataManager...")
            _data_directory_path = _resolve_data_directory()
            try:
                self._instance = DataManager(
                    base_data_path=_data_directory_path, preload=True
                )
                # print(
                #     f"Shared Car VA DataManager instance created successfully. "
                #     f"Data path: {_data_directory_path}"
                # )
            except Exception as e:
                # print(
                #     "FATAL ERROR: Could not initialize shared Car VA DataManager.",
                #     file=sys.stderr,
                # )
                # print(f"Base data path used: {_data_directory_path}", file=sys.stderr)
                # print(f"Error Type: {type(e).__name__}", file=sys.stderr)
                # print(f"Error Message: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                raise RuntimeError("Failed to initialize critical DataManager") from e
        return self._instance

    def __getattr__(self, name):
        return getattr(self._get_instance(), name)

    def __repr__(self):
        if self._instance is None:
            return "<LazyDataManager (not yet initialized)>"
        return repr(self._instance)


car_va_data_manager = _LazyDataManager()

# Make the instance easily importable from the 'data' package
__all__ = [
    "car_va_data_manager",
    "DataManager",
]  # Expose both the instance and the class type

from typing import Any

FOLDER_PATH = os.path.dirname(__file__)


def load_data() -> dict[str, Any]:
    """Legacy stub — kept for backward compatibility with Env base class."""
    return {}
