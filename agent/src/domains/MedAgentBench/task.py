from typing import List, Optional
import json
from pydantic import Field
from domains.task_base import BaseTask
from config.logger import LOGGER
from config.loader import CONFIG

simulation_config = CONFIG.SIMULATION


class Task(BaseTask):
    id: str = Field(description="Unique identifier for the task")
    goal: str = Field(description="The main goal of the user")
    additional_info: str = Field(
        description="Additional information that might be relevant to the task"
    )
    ref_MRN: Optional[str] = Field(
        description="The MRN of the patient involved in this task"
    )
    from_original_benchmark: bool = Field(
        description="Whether this task is from the original benchmark"
    )
    original_bench_task: Optional[int] = Field(
        description="The original benchmark task number, if applicable"
    )
    golden_answer: Optional[str] = Field(
        description="The golden answer for this task, if available"
    )

    @classmethod
    def load_from_original_benchmark(cls, data: dict) -> "Task":
        id = data.get("id", "")
        assert isinstance(id, str), "Task ID must be a string."
        assert id.startswith("task"), "Task ID must start with 'task'."
        task_type = id.split("task")[-1].split("_")[0]
        try:
            task_type_int = int(task_type)
            assert 1 <= task_type_int <= 10, "Task type must be between 1 and 10."
        except (ValueError, AssertionError) as e:
            raise ValueError(
                f"Invalid task ID format: {id}. Expected format 'taskXX_YY' where XX is an integer between 1 and 10."
            ) from e
        return cls(
            id=data.get("id", ""),
            goal=data.get("instruction", ""),
            additional_info=data.get("context", "No additional info provided."),
            ref_MRN=data.get("eval_MRN", ""),
            from_original_benchmark=True,
            original_bench_task=task_type_int,
            golden_answer=data.get("sol", [None])[0],
        )

    def __str__(self) -> str:
        return (
            f"Task ID: {self.id}\n"
            f"Goal: {self.goal}\n"
            f"Additional Info: {self.additional_info}\n"
            f"Reference MRN: {self.ref_MRN}\n"
            f"From Original Benchmark: {self.from_original_benchmark}\n"
            f"Original Benchmark Task Number: {self.original_bench_task}\n"
            f"Golden Answer: {self.golden_answer}"
        )


def _load_original_benchmark() -> List[Task]:
    path = simulation_config.TASK_FILE
    assert isinstance(path, str), "Task file path must be a string."
    with open(path, "r") as f:
        data = json.load(f)
    res = [Task.load_from_original_benchmark(item) for item in data]
    LOGGER.info(f"Loaded {len(res)} tasks from the original benchmark.")
    return res[:2]


def load_tasks() -> List[Task]:
    """
    Load tasks for the MedAgentBench domain.
    """
    assert isinstance(simulation_config.TYPE, str), "Simulation type must be a string."
    if simulation_config.TYPE == "Original_Benchmark":
        return _load_original_benchmark()
    else:
        raise ValueError(f"Unsupported simulation type: {simulation_config.TYPE}")
