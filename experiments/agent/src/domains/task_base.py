from pydantic import BaseModel, Field
from typing import List


class BaseTask(BaseModel):
    id: str = Field(description="Unique identifier for the task")

    def task_arg(self) -> List[str]:
        return []
