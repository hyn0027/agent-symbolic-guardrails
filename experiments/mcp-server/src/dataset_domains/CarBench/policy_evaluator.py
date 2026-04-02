import contextvars
from typing import List


policy_errors_during_runtime: contextvars.ContextVar[List[str]] = (
    contextvars.ContextVar("policy_errors_during_runtime")
)
