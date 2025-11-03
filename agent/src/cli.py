from agent import ReActAgent
from config.loader import CONFIG
from config.logger import LOGGER


def main():
    LOGGER.debug(f"Configuration Loaded: {CONFIG}")
    agent = ReActAgent()
    initial_message = agent.initiate_conversation()
    LOGGER.info(f"Agent: {initial_message}")
    while True:
        user_input = input("User: ")
        LOGGER.debug(f"User: {user_input}")
        if user_input.lower() in ["exit", "quit"]:
            LOGGER.info("Exiting the agent.")
            break
        response = agent.ReAct_loop(user_input)
        LOGGER.info(f"Agent: {response}")


if __name__ == "__main__":
    main()
