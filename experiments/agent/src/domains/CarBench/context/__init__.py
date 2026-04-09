from .fixed_context import FixedContext, fixed_context
from .dynamic_context_state import ContextState, context_state
from domains.CarBench.task import Task


def load_context(task: Task) -> None:
    default_fixed_context = FixedContext()
    fixed_context.set(default_fixed_context)
    fixed_context.get().update_state(**task.context_init_config)

    default_context_state = ContextState()
    context_state.set(default_context_state)
    context_state.get().update_state(**task.context_init_config)
    return
