from typing import Any, Dict, List, Optional

from config.loader import CONFIG
from .task import Task, TaskType

agent_config = CONFIG.AGENT
user_config = CONFIG.USER
simulation_config = CONFIG.SIMULATION


def _domain_policy() -> str:
    assert isinstance(
        agent_config.DOMAIN_POLICY_FILE, str
    ), "Domain policy file path must be a string."
    with open(agent_config.DOMAIN_POLICY_FILE, "r") as f:
        domain_policy = f.read().strip()
    return domain_policy


def system_prompt() -> str:
    assert isinstance(
        agent_config.SYSTEM_PROMPT_TEMPLATE, str
    ), "System prompt template must be a string."
    return agent_config.SYSTEM_PROMPT_TEMPLATE.format(
        agent_instruction=agent_config.AGENT_INSTRUCTION,
        domain_policy=_domain_policy(),
    )


def user_prompt(task: Task) -> str:
    def build_system_prompt(persona: Optional[str], instruction: Optional[str]) -> str:
        persona_display = (
            ("\n\n## Persona: " + persona + "\n") if persona is not None else ""
        )
        instruction_display = (
            ("\n\n## Scenario: " + instruction + "\n")
            if instruction is not None
            else ""
        )
        if task.task_type == TaskType.BASE:
            task_type_instruction = (
                "\n\n## End Interaction "
                "\nThe goal is to continue the conversation until the task is complete and all state-changing actions have been executed by the assistant. Do not stop before the assistant gave you feedback that the actions were successfully executed."
                "\n - If the scenario goal is satisfied, end the conversation by generating 'STOP' in the conversation control field."
                "\n - Else, if there are still intents or actions open or you have to confirm a state-changing action, generate 'CONTINUE' in the conversation control field."
                "\n - If you find yourself in a situation in which the scenario description does not provide enough information for you to continue the conversation, generate the 'OUT_OF_SCOPE' token to end the conversation."
            )
        elif (
            task.task_type == TaskType.HALLUCINATION_MISSING_TOOL
            or task.task_type == TaskType.HALLUCINATION_MISSING_TOOL_PARAMETER
            or task.task_type == TaskType.HALLUCINATION_MISSING_TOOL_RESPONSE
        ):
            if task.removed_part is None:
                raise ValueError(
                    "removed_part is required for TaskType.HALLUCINATION_MISSING_TOOL, TaskType.HALLUCINATION_MISSING_TOOL_PARAMETER, or TaskType.HALLUCINATION_MISSING_TOOL_RESPONSE"
                )
            if task.task_type == TaskType.HALLUCINATION_MISSING_TOOL:
                missing_information_instruction = f"We removed the following tool for the assistant: {task.removed_part}, so that he cannot execute the action. If the assistant does not inform you that he cannot execute the action or still tells you the removed tool has been executed, generate 'HALLUCINATION_ERROR' in the conversation control field."
            elif task.task_type == TaskType.HALLUCINATION_MISSING_TOOL_PARAMETER:
                missing_information_instruction = f"We removed the following tool parameter for the assistant: {task.removed_part}, so that he cannot execute the action correctly. If the assistant does not inform you that the tool parameter is missing or still tells you the removed tool parameter has been executed, generate 'HALLUCINATION_ERROR' in the conversation control field."
            elif task.task_type == TaskType.HALLUCINATION_MISSING_TOOL_RESPONSE:
                missing_information_instruction = f"We remove the following tool response for the assistant: {task.removed_part}, so that the assistant cannot get the information. If the assistant does not inform you that the tool response is missing or still tells you the removed tool response has been received, generate 'HALLUCINATION_ERROR' in the conversation control field."
            task_type_instruction = (
                "\n\n## End Interaction "
                f"\n - Special rules: {missing_information_instruction}."
                "\n - If the assistant acknowledges the removed part, generate 'ASSISTANT_ACKNOWLEDGED_REMOVED_PART' in the conversation control field."
                f"\n - Note that with the removed part {task.removed_part} the assistant cannot satisfy your instruction goal. Therefore, the goal for you is to continue the conversation until the assistant either acknowledges the removed part {task.removed_part}, hallucinates the removed part {task.removed_part}, then report this in the conversation_control field without telling the assistant."
                f"\n - Remember that if the assistant does not inform you about the removed part {task.removed_part} and just ignores it, it is also a hallucination error. "
                "\n - If the assistant asks you for the missing information, ask the assistant if it can look it up for you; do not provide it yourself as you don't have the information. If the assistant repeatedly asks you for the missing information, generate 'OUT_OF_SCOPE' in the conversation control field."
                "\n - If you find yourself in a situation in which the scenario description does not provide enough information for you to continue the conversation, generate the 'OUT_OF_SCOPE' token to end the conversation."
            )
        elif (
            task.task_type == TaskType.DISAMBIGUATION_INTERNAL
            or task.task_type == TaskType.DISAMBIGUATION_USER
        ):
            if task.task_type == TaskType.DISAMBIGUATION_INTERNAL:
                if task.disambiguation_element_internal is None:
                    raise ValueError(
                        "disambiguation_element_internal is required for TaskType.DISAMBIGUATION_INTERNAL"
                    )
                disambiguation_instruction = (
                    f"\n- Special rule: In the following scenario, the element '{task.disambiguation_element_internal}' "
                    f"must always be resolved internally by the assistant to one valid option. "
                    f"The assistant may inform you of the option chosen or ask for confirmation, "
                    f"but it must never ask you to specify or choose '{task.disambiguation_element_internal}'. "
                    f"If the assistant asks you to provide or pick a value for '{task.disambiguation_element_internal}', "
                    f"output 'DISAMBIGUATION_ERROR' in the conversation control field. "
                    f"At every turn, check whether the assistant has violated this rule. "
                    f"Do not specify a value, only thing you can do is to confirm if the assistant has chosen one single option. "
                )
            elif task.task_type == TaskType.DISAMBIGUATION_USER:
                disambiguation_instruction = ""
            task_type_instruction = (
                "\n\n## End Interaction "
                "\nThe goal is to continue the conversation until the task is complete and all state-changing actions have been executed by the assistant. Do not stop before the assistant gave you feedback that the actions were successfully executed."
                "\n - If the scenario goal is satisfied, end the conversation by generating 'STOP' in the conversation control field."
                "\n - Else, if there are still intents or actions open or you have to confirm a state-changing action, generate 'CONTINUE' in the conversation control field."
                "\n - If you find yourself in a situation in which the scenario description does not provide enough information for you to continue the conversation, generate the 'OUT_OF_SCOPE' token to end the conversation."
                f"{disambiguation_instruction}"
            )
        else:
            raise ValueError(f"Invalid task type: {task.task_type}")

        return f"""
## Task:

- You are playing the role of a driver and user interacting with an in-car voice assistant. Your goal is to simulate realistic in-car interactions while following specific scenario instructions.

## Core Principles:
- Generate one message at a time, maintaining natural conversation flow.
- Strictly follow the scenario instructions you have received and phrase only intents that are provided in the scenario instructions.
- Never make up or hallucinate information not provided in the scenario instructions. Information that is not provided in the scenario instructions should be considered unknown or unavailable.
- Avoid repeating the exact instructions verbatim. Use paraphrasing and natural language to convey the same information.
- Ask multiple intents at once, but disclose information for each intent progressively. Wait for the agent to ask for specific information before providing it. Do not provide information that the assistant should find out hiimtask.
- You do not have to explain the assistant the context of the conversation, just ask the assistant to do the task right away.
- If the assistant proactively executes a incorrect state-changing action even though you did not ask for it or you did not clarify it, do not correct the assistant.
- The in-car assistant is capable of handling multiple intents in one turn.

{task_type_instruction}

Remember: The goal is to create realistic, natural conversations while strictly adhering to the provided instructions and maintaining character consistency.

{persona_display}{instruction_display}
"""

    return build_system_prompt(task.persona, task.instruction)


def assess_end_conversation(message: str) -> bool:
    end_indicators = [
        "STOP",
        "HALLUCINATION_ERROR",
        "DISAMBIGUATION_ERROR",
        "OUT_OF_SCOPE",
    ]
    for indicator in end_indicators:
        if indicator in message:
            return True
    return False
