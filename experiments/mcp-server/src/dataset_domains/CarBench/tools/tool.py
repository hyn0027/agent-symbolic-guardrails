import abc
from typing import Any, Dict, List
from mcp_server import mcp
import functools
import inspect
import json
from .evaluator import append_current_state_hash
from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)

from config_loader import CONFIG

safeguard_config = CONFIG.SAFEGUARD


class Tool(abc.ABC):
    all_tool_calls = []
    raise_count_with_type = {
        "implemented": 0,
        "api_check": 0,
        "api_check, api_redesign": 0,
    }

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        if cls is Tool:
            return

        raw = cls.__dict__.get("invoke")
        if raw is None:
            raise TypeError(f"{cls.__name__} must define invoke()")

        # unwrap staticmethod/classmethod to the real function
        if isinstance(raw, staticmethod):
            original_invoke = raw.__func__
            wrap_back = staticmethod
        elif isinstance(raw, classmethod):
            original_invoke = raw.__func__
            wrap_back = classmethod
        else:
            original_invoke = raw
            wrap_back = lambda f: f

        @functools.wraps(original_invoke)
        def wrapped_invoke(*args, **kwargs) -> Any:
            result = original_invoke(*args, **kwargs)
            cls.after_invoke(result, *args, **kwargs)
            return result

        wrapped_invoke.__signature__ = inspect.signature(original_invoke)

        cls.invoke = wrap_back(wrapped_invoke)

    @staticmethod
    def invoke(*args, **kwargs) -> Any:
        raise NotImplementedError

    @staticmethod
    def get_info() -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def register_tool(cls) -> None:
        info = cls.get_info()["function"]
        mcp.tool(
            cls.invoke,
            name=info["name"],
            description=info["description"],
            meta=cls.get_metadata(),
        )

    @classmethod
    def after_invoke(cls, result, *args, **kwargs) -> None:
        append_current_state_hash()
        result = json.loads(result) if isinstance(result, str) else result
        if result["status"] == "SUCCESS":
            cls.all_tool_calls.append(
                {
                    "name": cls.get_info()["function"]["name"],
                    "args": args,
                    "kwargs": kwargs,
                    "result": result,
                }
            )
        elif result["status"] == "FAILURE":
            cls.raise_count_with_type["implemented"] += 1
        elif result["status"] == "REJECTED_BY_GUARDRAIL":
            cls.raise_count_with_type["api_check"] += 1

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        info = cls.get_info()["function"]
        name = info["name"]
        metadata = {
            "overwrite_input_schema": info["parameters"],
        }

        if info["description"].startswith("REQUIRES_CONFIRMATION"):
            metadata["require_confirmation"] = (
                safeguard_config.USER_CONFIRMATION
            )  # LLM-POL:004
        if name in ["open_close_window"]:  # LLM-POL:007
            metadata["require_confirmation"] = (
                safeguard_config.USER_CONFIRMATION
            )

        return metadata


@mcp.tool(
    meta={
        "disclose_to_model": False,
    }
)
def get_user_confirmation_details(func_name, func_args: Dict[str, Any]) -> str:
    """
    Get details for user confirmation. For test only.
    """
    vehicle_ctx = context_state.get()
    if func_name == "open_close_window":  # LLM-POL:007
        percentage = func_args.get("percentage")
        ac = vehicle_ctx.air_conditioning
        if percentage > 25 and ac:
            return f"Warning: You are about to open the window more than 25% while the AC is ON, which may lead to energy inefficiency."
        return f"You are about to open the window to {percentage}%. Air conditioning is currently {'ON' if ac else 'OFF'}."

    return ""


@mcp.tool(
    meta={
        "disclose_to_model": False,
    }
)
def save_state(path: str) -> str:
    raise NotImplementedError(
        "This function is only for testing. It should not be called during actual evaluation."
    )


@mcp.tool(
    meta={
        "disclose_to_model": False,
    }
)
def load_state(path: str) -> str:
    raise NotImplementedError(
        "This function is only for testing. It should not be called during actual evaluation."
    )


@mcp.tool(
    meta={
        "disclose_to_model": False,
    }
)
def report_error_statistics() -> Dict:
    res = {}
    for error_type, count in Tool.raise_count_with_type.items():
        if count > 0:
            res[error_type] = count
    return {"raise_count_with_type": res}
