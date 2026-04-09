from .tools import *
from config_loader import CONFIG
from .context.fixed_context import FixedContext, fixed_context
from .context.dynamic_context_state import ContextState, context_state
from .tools.tool_execution_error_evaluator import tool_execution_errors_during_runtime
from .policy_evaluator import policy_errors_during_runtime
from .tasks.task_config import TaskConfig, task_config
import json


# set context_init_config
def _load_context() -> None:
    assert isinstance(CONFIG.IDX, str), "Config idx must be a string."
    assert isinstance(CONFIG.DATASET.PATH, str), "Dataset path must be a string."

    with open(CONFIG.DATASET.PATH, "r") as f:
        for line in f:
            task = json.loads(line)
            if task["task_id"] == CONFIG.IDX:
                context_init_config = json.loads(task["context_init_config"])

                default_fixed_context = FixedContext()
                fixed_context.set(default_fixed_context)
                fixed_context.get().update_state(**context_init_config)

                default_context_state = ContextState()
                context_state.set(default_context_state)
                context_state.get().update_state(**context_init_config)

                default_task_config = TaskConfig()
                task_config.set(default_task_config)
                task_config.get().update_state(calendar_id=task["calendar_id"])

                tool_execution_errors_during_runtime.set([])
                policy_errors_during_runtime.set([])
                return
    raise ValueError(f"Task with id {CONFIG.IDX} not found in dataset.")


_load_context()


# print("invoking GetLocationIdByLocationName with input 'Stuttgart'...")
# GetLocationIdByLocationName.invoke("Stuttgart")
# print("Finished invoking GetLocationIdByLocationName.")
