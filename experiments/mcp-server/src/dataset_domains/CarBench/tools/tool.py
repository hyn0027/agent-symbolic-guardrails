import abc
from typing import Any
from mcp_server import mcp


class Tool(abc.ABC):
    @staticmethod
    def invoke(*args, **kwargs):
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
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "overwrite_input_schema": cls.get_info()["function"]["parameters"],
        }
