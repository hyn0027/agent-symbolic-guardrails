# Modified from tau2 bench

import json
import textwrap
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field
from typing_extensions import Annotated
from domains.task_base import BaseTask

from config.loader import CONFIG


class Description(BaseModel):
    """
    Description of a scenario. This can be sent to the evaluator.
    """

    purpose: Annotated[
        Optional[str],
        Field(description="Explains what the scenario is testing.", default=None),
    ]
    relevant_policies: Annotated[
        Optional[str],
        Field(
            description="The part of the policy that is relevant to the scenario.",
            default=None,
        ),
    ]
    notes: Annotated[
        Optional[str],
        Field(
            description="Any additional information about the scenario that is not covered by the other fields.",
            default=None,
        ),
    ]

    def __str__(self) -> str:
        lines = []
        if self.purpose is not None:
            lines.append(f"Purpose: {self.purpose}")
        if self.relevant_policies is not None:
            lines.append(f"Relevant Policies: {self.relevant_policies}")
        if self.notes is not None:
            lines.append(f"Notes: {self.notes}")
        return "\n".join(lines)


class StructuredUserInstructions(BaseModel):
    """
    User instructions. This information defines the specific situation the user is in and the tasks they are trying to complete.
    """

    domain: Annotated[str, Field(description="The domain of the task.")]
    reason_for_call: Annotated[
        str, Field(description="The reason for the user to call the agent.")
    ]
    known_info: Annotated[
        Optional[str],
        Field(description="Known information about the user.", default=None),
    ]
    unknown_info: Annotated[
        Optional[str],
        Field(description="Unknown information about the user.", default=None),
    ]
    task_instructions: Annotated[str, Field(description="Instructions for the User.")]

    def __str__(self) -> str:
        lines = []
        tab = "\t"
        lines.append(f"Domain: {self.domain}")
        lines.append(f"Reason for call:\n{textwrap.indent(self.reason_for_call, tab)}")
        if self.known_info is not None:
            lines.append(f"Known info:\n{textwrap.indent(self.known_info, tab)}")
        if self.unknown_info is not None:
            lines.append(f"Unknown info:\n{textwrap.indent(self.unknown_info, tab)}")
        lines.append(
            f"Task instructions:\n{textwrap.indent(self.task_instructions, tab)}"
        )
        return "\n".join(lines)


UserInstructions = StructuredUserInstructions | str


class UserScenario(BaseModel):
    """
    User scenario. All the information that will be sent to the user simulator.
    """

    persona: Annotated[
        Optional[str],
        Field(
            description="User's persona. This information defines the user in general, not the specific situation they are in.",
            default=None,
        ),
    ]
    instructions: Annotated[
        UserInstructions,
        Field(
            description="Instructions for the User. This information defines the specific situation the user is in and the tasks they are trying to complete."
        ),
    ]

    def __str__(self) -> str:
        lines = []
        if self.persona is not None:
            lines.append("Persona:")
            lines.append(textwrap.indent(self.persona, "\t"))
        lines.append("Instructions:")
        lines.append(textwrap.indent(str(self.instructions), "\t"))
        return "\n".join(lines)


class ToolCall(BaseModel):
    """
    A tool call.
    """

    id: str = Field(default="", description="The unique identifier for the tool call.")
    name: str = Field(description="The name of the tool.")
    arguments: dict = Field(description="The arguments of the tool.")

    def __str__(self) -> str:
        lines = [f"ToolCall"]
        if self.id:
            lines.append(f"id: {self.id}")
        lines.append(f"name: {self.name}")
        lines.append(f"arguments:\n{json.dumps(self.arguments, indent=2)}")
        return "\n".join(lines)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ToolCall):
            return False
        return (
            self.id == other.id
            and self.name == other.name
            and self.arguments == other.arguments
        )


class Action(BaseModel):
    """
    An Agent/User action.
    Example:
      {
      "action_id": "get_user_details_1",
      "name": "get_user_details",
      "arguments": { "user_id": "sophia_silva_7557", "note": "I need to get the user details for user_id: sophia_silva_7557" },
      "compare_args": ["user_id"]
    },
    A tool call can be compared with an action by comparing the arguments in compare_args.
    If compare_args is None, will check all the arguments.
    """

    action_id: str = Field(
        description="The unique identifier for the action within a scenario."
    )
    name: str = Field(description="The name of the action.")
    arguments: dict = Field(description="The arguments for the action.")
    info: Optional[str] = Field(
        description="Information about the action.", default=None
    )
    compare_args: Optional[list[str]] = Field(
        description="The arguments to check in tool call. If None, will check all the arguments.",
        default=None,
    )

    def __str__(self) -> str:
        lines = []
        lines.append(f"Action ID: {self.action_id}")
        lines.append(f"Name: {self.name}")
        lines.append(f"Arguments:\n{json.dumps(self.arguments, indent=2)}")
        if self.info is not None:
            lines.append(f"Info:\n{textwrap.indent(self.info, '    ')}")
        return "\n".join(lines)

    def compare_with_tool_call(self, tool_call: ToolCall) -> bool:
        """
        Compare the action with a tool call.
        If the name is not the same, return False.
        If compare_args is None, will check all the arguments.
        Otherwise, will check only the arguments in compare_args.
        """
        if self.name != tool_call.name:
            return False
        if self.compare_args is None:
            compare_args = list(self.arguments.keys())
        else:
            compare_args = self.compare_args
        if len(compare_args) == 0:
            return True
        tool_args = {k: v for k, v in tool_call.arguments.items() if k in compare_args}
        action_args = {k: v for k, v in self.arguments.items() if k in compare_args}
        for k in compare_args:
            if k not in tool_args or k not in action_args:
                return False
            if isinstance(action_args[k], float) and isinstance(tool_args[k], float):
                if abs(action_args[k] - tool_args[k]) > 1e-6:
                    return False
            elif isinstance(action_args[k], list) and isinstance(tool_args[k], list):
                action_args[k] = [str(item) for item in action_args[k]]
                tool_args[k] = [str(item) for item in tool_args[k]]
                if sorted(action_args[k]) != sorted(tool_args[k]):
                    return False
            else:
                if tool_args[k] != action_args[k]:
                    return False
        return True


class RewardType(str, Enum):
    DB = "DB"
    ENV_ASSERTION = "ENV_ASSERTION"
    NL_ASSERTION = "NL_ASSERTION"
    ACTION = "ACTION"
    COMMUNICATE = "COMMUNICATE"


class EvaluationCriteria(BaseModel):
    """
    Evaluation criteria for a particular task. This will be sent to the evaluator.
    """

    actions: Annotated[
        Optional[list[Action]],
        Field(
            description="The actions that the agent should take to complete the task.",
            default=None,
        ),
    ]

    destructive_actions: Annotated[
        Optional[list[Action]],
        Field(
            description="All the destructive actions that the agent is expected to take during the task.",
            default=None,
        ),
    ]

    communicate_info: Annotated[
        Optional[list[str]],
        Field(
            description="List of information that the agent should communicate to the user.",
            default=None,
        ),
    ]

    nl_assertions: Annotated[
        Optional[list[str]],
        Field(
            description="List of assertions for the task, in natural language.",
            default=None,
        ),
    ]

    reward_basis: Annotated[
        list[RewardType],
        Field(
            description="The basis of the reward. This will be used to determine the reward for the task.",
            default_factory=lambda: [RewardType.DB, RewardType.COMMUNICATE],
        ),
    ]

    def __str__(self) -> str:
        lines = []
        if self.actions is not None:
            lines.append("Actions:")
            lines.extend(
                [textwrap.indent(str(action), "\t") for action in self.actions]
            )
        if self.communicate_info is not None:
            lines.append("Communicate Info:")
            lines.extend(
                [textwrap.indent(info, "\t") for info in self.communicate_info]
            )
        if self.nl_assertions is not None:
            lines.append("NL Assertions:")
            lines.extend(
                [textwrap.indent(assertion, "\t") for assertion in self.nl_assertions]
            )
        return "\n".join(lines)


class Task(BaseTask):
    """
    A task for a particular domain. This will be sent to the user simulator, the environment and the evaluator.
    """

    id: str = Field(description="The unique identifier for the task.")
    description: Annotated[
        Optional[Description],
        Field(
            description="Description of the task. This can be sent to the evaluator.",
            default=None,
        ),
    ]
    user_scenario: Annotated[
        UserScenario,
        Field(
            description="User scenario. This information will be sent to the user simulator."
        ),
    ]
    ticket: Annotated[
        Optional[str],
        Field(
            description="Task in ticket format for solo agent solving.",
            default=None,
        ),
    ]
    evaluation_criteria: Annotated[
        Optional[EvaluationCriteria],
        Field(
            description="Evaluation criteria for the task. This will be sent to the evaluator.",
            default=None,
        ),
    ]

    def __str__(self) -> str:
        lines = []
        lines.append(f"ID: {self.id}")
        if self.description is not None:
            lines.append("Description:")
            lines.append(textwrap.indent(str(self.description), "\t"))
        lines.append("User Scenario:")
        lines.append(textwrap.indent(str(self.user_scenario), "\t"))
        if self.evaluation_criteria is not None:
            lines.append("Evaluation Criteria:")
            lines.append(textwrap.indent(str(self.evaluation_criteria), "\t"))
        return "\n".join(lines)


def _load_tasks_from_json_file(file_path: str) -> List[Task]:
    """
    Load tasks from a JSON file.
    """
    with open(file_path, "r") as f:
        tasks_json = json.load(f)
    tasks = [Task.model_validate(task_json, strict=True) for task_json in tasks_json]
    return tasks


def load_tasks() -> List[Task]:
    """
    Load tasks based on the configuration.
    """
    assert isinstance(CONFIG.SIMULATION.TASK_FILE, str), "TASK_FILE should be a string."

    task_file = CONFIG.SIMULATION.TASK_FILE
    return _load_tasks_from_json_file(task_file)
