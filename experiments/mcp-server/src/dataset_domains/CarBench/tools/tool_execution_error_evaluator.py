import contextvars
from typing import List
from mcp_server import mcp

tool_execution_errors_during_runtime: contextvars.ContextVar[List[str]] = (
    contextvars.ContextVar("tool_execution_errors_during_runtime")
)


@mcp.tool(
    meta={
        "disclose_to_model": False,
    }
)
def get_tool_execution_errors_during_runtime() -> List[str]:
    return tool_execution_errors_during_runtime.get()
