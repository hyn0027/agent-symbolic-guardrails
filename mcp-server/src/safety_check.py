from typing import List
from config_loader import CONFIG
from mcp_server import mcp
import inspect

error_handling_config = CONFIG.ERROR_HANDLING

raise_count_with_type = {}
error_calling_log = []


def process_error(message, err_type: List[str]) -> None:
    raise_count_with_type_key = ",".join(sorted(err_type))
    if raise_count_with_type_key not in raise_count_with_type:
        raise_count_with_type[raise_count_with_type_key] = 0
    raise_count_with_type[raise_count_with_type_key] += 1
    stack = inspect.stack()
    caller_frame = stack[1]
    error_calling_log.append(
        {
            "message": message,
            "error_types": err_type,
            "caller_function": caller_frame.function,
            "caller_line_no": caller_frame.lineno,
        }
    )
    if error_handling_config.CONTINUE_ON_ERROR:
        if "implemented" in err_type:
            raise ValueError(message)
        else:
            print(f"Warning: {message} | Error Types: {err_type}")
    else:
        raise ValueError(message)


@mcp.tool(
    meta={
        "disclose_to_model": False,
    }
)
def report_error_statistics() -> dict:
    return {
        "raise_count_with_type": raise_count_with_type,
        "error_calling_log": error_calling_log,
    }
