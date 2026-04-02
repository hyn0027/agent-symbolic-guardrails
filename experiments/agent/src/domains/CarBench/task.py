from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel
from domains.task_base import BaseTask
import json
from config.logger import LOGGER
from config.loader import CONFIG

simulation_config = CONFIG.SIMULATION


class Action(BaseModel):
    name: str
    kwargs: Dict[str, Any]
    index: Optional[int] = None
    dependent_on_action_index: Optional[Union[int, List[int]]] = None

    def __str__(self) -> str:
        return "\t\n".join(
            [
                f"Action Name: {self.name}",
                f"Action Kwargs: {json.dumps(self.kwargs)}",
                f"Action Index: {self.index}",
                f"Dependent on Action Index: {self.dependent_on_action_index}",
            ]
        )


class TaskType(str, Enum):
    BASE = "base"
    HALLUCINATION_MISSING_TOOL = "hallucination_missing_tool"
    HALLUCINATION_MISSING_TOOL_PARAMETER = "hallucination_missing_tool_parameter"
    HALLUCINATION_MISSING_TOOL_RESPONSE = "hallucination_missing_tool_response"
    DISAMBIGUATION_INTERNAL = "disambiguation_internal"
    DISAMBIGUATION_USER = "disambiguation_user"


class Task(BaseTask):
    task_id: str  # also id
    calendar_id: str
    actions: List[Action]
    persona: str
    instruction: str
    context_init_config: Dict[str, Any]
    task_type: TaskType
    disambiguation_element_internal: Optional[str] = None
    disambiguation_element_user: Optional[str] = None
    disambiguation_element_note: Optional[str] = None
    removed_part: Optional[List[str]] = None

    def __str__(self) -> str:
        return "\n".join(
            [
                f"Task ID: {self.task_id}",
                f"Calendar ID: {self.calendar_id}",
                f"Persona: {self.persona}",
                f"Instruction: {self.instruction}",
                f"Context Init Config: {json.dumps(self.context_init_config)}",
                f"Task Type: {self.task_type}",
                f"Disambiguation Element Internal: {self.disambiguation_element_internal}",
                f"Disambiguation Element User: {self.disambiguation_element_user}",
                f"Disambiguation Element Note: {self.disambiguation_element_note}",
                f"Removed Part: {self.removed_part}",
                f"Actions: {json.dumps([str(action) for action in self.actions], indent=2)}",
            ]
        )


def load_tasks() -> List[Task]:
    path = simulation_config.TASK_FILE
    assert isinstance(path, str), "Task file path must be a string."
    # read jsonl
    tasks = []
    with open(path, "r") as f:
        for line in f:
            data = json.loads(line)
            data["actions"] = json.loads(data["actions"])
            data["context_init_config"] = json.loads(data["context_init_config"])
            try:
                task = Task(id=data["task_id"], **data)
                tasks.append(task)
            except Exception as e:
                LOGGER.error(f"Error loading task from line: {line}")
                LOGGER.exception(e)
    LOGGER.info(f"Loaded {len(tasks)} tasks from {path}")
    return tasks
