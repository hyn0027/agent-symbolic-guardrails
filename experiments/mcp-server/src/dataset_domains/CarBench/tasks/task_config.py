import contextvars
import threading

from pydantic import BaseModel, Field, ConfigDict

# A ContextVar that will hold the current VehicleContext for the running task.
task_config: contextvars.ContextVar["TaskConfig"] = contextvars.ContextVar(
    "task_config"
)


class TaskConfig(BaseModel):
    calendar_id: str = Field(default=None, description="Id of the task")

    # class Config:
    #     validate_assignment = True
    model_config = ConfigDict(validate_assignment=True)

    def __init__(self, **data):
        super().__init__(**data)
        self._lock = threading.Lock()

    def update_state(self, **kwargs):
        with self._lock:
            for key in kwargs.keys():
                if not hasattr(self, key):
                    raise ValueError(f"Invalid attribute: {key}")
            for key, value in kwargs.items():
                setattr(self, key, value)
