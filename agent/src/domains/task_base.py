from pydantic import BaseModel, Field


class BaseTask(BaseModel):
    id: str = Field(description="Unique identifier for the task")
