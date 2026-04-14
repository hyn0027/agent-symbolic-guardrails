import abc
from typing import Any, Dict, List
from mcp_server import mcp
import functools
import inspect
import json
from .evaluator import append_current_state_hash

from dataset_domains.CarBench.context.dynamic_context_state import (
    ContextState,
    context_state,
)
from dataset_domains.CarBench.context.fixed_context import FixedContext, fixed_context
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
        if "status" not in result:
            return
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
            if safeguard_config.RAISE_ERROR_IF_FAILED:
                raise ValueError(result["errors"])
        elif result["status"] == "REJECTED_BY_GUARDRAIL":
            cls.raise_count_with_type["api_check"] += 1
            if safeguard_config.RAISE_ERROR_IF_FAILED:
                raise ValueError(result["errors"])

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
            metadata["require_confirmation"] = safeguard_config.USER_CONFIRMATION
        if name in ["open_close_sunroof", "set_fog_lights"]:  # LLM-POL:008, AUT-POL:009
            metadata["require_confirmation"] = safeguard_config.USER_CONFIRMATION
        if name in ["set_climate_temperature"]:  # LLM-POL:012
            metadata["require_confirmation"] = safeguard_config.USER_CONFIRMATION
        if name in [
            "get_current_navigation_state",
            "get_routes_from_start_to_destination",
        ]:  # LLM-POL:021
            metadata["tool_call_disclosure"] = safeguard_config.TOOL_CALL_DISCLOSURE
            # LLM-POL:022
            metadata["require_confirmation"] = safeguard_config.USER_CONFIRMATION
        return metadata


@mcp.tool(
    meta={
        "disclose_to_model": False,
    }
)
def save_state(path: str) -> str:
    vehicle_ctx = context_state.get()
    fixed_ctx = fixed_context.get()
    state = {
        "vehicle_context": vehicle_ctx.model_dump(mode="json"),
        "fixed_context": fixed_ctx.model_dump(mode="json"),
    }
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    return "State saved successfully."


@mcp.tool(
    meta={
        "disclose_to_model": False,
    }
)
def load_state(path: str) -> str:
    with open(path, "r") as f:
        state = json.load(f)
    # vehicle_ctx = ContextState.model_validate(state["vehicle_context"])
    # fixed_ctx = FixedContext.model_validate(state["fixed_context"])
    context_state.get().update_state(**state["vehicle_context"])
    fixed_context.get().update_state(**state["fixed_context"])
    return "State loaded successfully."


@mcp.tool(
    meta={
        "disclose_to_model": False,
    }
)
def get_vehicle_ctx() -> Dict:
    return context_state.get()


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
