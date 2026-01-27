from config.loader import CONFIG

agent_config = CONFIG.AGENT
user_config = CONFIG.USER


def _domain_policy() -> str:
    return ""
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


def user_prompt(task) -> str:
    raise NotImplementedError("User prompt generation is not implemented yet.")


def assess_end_conversation(message: str) -> bool:
    end_indicators = ["###STOP###"]
    for indicator in end_indicators:
        if indicator in message:
            return True
    return False
