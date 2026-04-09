import abc
from typing import Any
from mcp_server import mcp
import functools
import inspect
from .evaluator import append_current_state_hash


class Tool(abc.ABC):
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

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "overwrite_input_schema": cls.get_info()["function"]["parameters"],
        }
