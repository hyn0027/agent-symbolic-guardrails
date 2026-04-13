import contextvars
from typing import List
from mcp_server import mcp


policy_errors_during_runtime: contextvars.ContextVar[List[str]] = (
    contextvars.ContextVar("policy_errors_during_runtime")
)


@mcp.tool(
    meta={
        "disclose_to_model": False,
    }
)
def get_policy_errors_during_runtime() -> List[str]:
    return policy_errors_during_runtime.get()
