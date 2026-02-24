from config.loader import CONFIG
from .task import Task

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
    assert isinstance(
        user_config.SYSTEM_PROMPT_TEMPLATE, str
    ), "User prompt template must be a string."
    if simulation_config.TYPE == "Original_Benchmark":
        return user_config.SYSTEM_PROMPT_TEMPLATE.format(
            task_goal=task.goal,
            additional_info=task.additional_info,
        )
    elif simulation_config.TYPE == "Generated_Data":
        return user_config.SYSTEM_PROMPT_TEMPLATE.format(
            task_goal=task.goal,
            additional_info=task.additional_info,
            policy=task.policy if task.policy is not None else "No policy provided.",
            explanation=(
                task.explanation
                if task.explanation is not None
                else "No explanation provided."
            ),
        )
    else:
        raise ValueError(f"Unsupported simulation type: {simulation_config.TYPE}")


def assess_end_conversation(message: str) -> bool:
    end_indicators = ["###STOP###"]
    for indicator in end_indicators:
        if indicator in message:
            return True
    return False
