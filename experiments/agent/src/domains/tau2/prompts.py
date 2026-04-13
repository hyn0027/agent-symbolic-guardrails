from config.loader import CONFIG
from .task import Task
from config.logger import LOGGER
from agent import ReActAgent
from typing import Optional

agent_config = CONFIG.AGENT
user_config = CONFIG.USER


def _domain_policy() -> str:
    assert isinstance(
        agent_config.DOMAIN_POLICY_FILE, str
    ), "DOMAIN_POLICY_FILE must be a string."
    with open(agent_config.DOMAIN_POLICY_FILE, "r") as f:
        domain_policy = f.read().strip()
    return domain_policy


def system_prompt(task: Optional[Task]) -> str:
    assert isinstance(
        agent_config.AGENT_INSTRUCTION, str
    ), "AGENT_INSTRUCTION must be a string."

    assert isinstance(
        agent_config.SYSTEM_PROMPT_TEMPLATE, str
    ), "SYSTEM_PROMPT_TEMPLATE must be a string."

    return agent_config.SYSTEM_PROMPT_TEMPLATE.format(
        agent_instruction=agent_config.AGENT_INSTRUCTION,
        domain_policy=_domain_policy(),
    )


def user_prompt(task: Task) -> str:
    assert isinstance(
        user_config.SIMULATION_GUIDELINE_PATH, str
    ), "SIMULATION_GUIDELINE_PATH must be a string."

    with open(user_config.SIMULATION_GUIDELINE_PATH, "r") as file:
        guidelines = file.read()

    assert isinstance(
        user_config.SYSTEM_PROMPT_TEMPLATE, str
    ), "SYSTEM_PROMPT_TEMPLATE must be a string."

    return user_config.SYSTEM_PROMPT_TEMPLATE.format(
        global_user_sim_guidelines=guidelines, instructions=task.user_scenario
    )


def assess_end_conversation(message: str, agent: ReActAgent) -> bool:
    end_indicators = [
        "###STOP###",
        # "###TRANSFER###",
        "###OUT-OF-SCOPE###",
    ]
    for indicator in end_indicators:

        if indicator in message:
            return True
    return False
