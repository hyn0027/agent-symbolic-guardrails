import contextvars
from typing import List

tool_execution_errors_during_runtime: contextvars.ContextVar[List[str]] = (
    contextvars.ContextVar("tool_execution_errors_during_runtime")
)
