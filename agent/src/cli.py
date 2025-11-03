from agent import ReActAgent
from config import CONFIG, LOGGER


def main():
    LOGGER.debug(f"Configuration Loaded: {CONFIG}")
    agent = ReActAgent()
    while True:
        user_input = input("User: ")
        LOGGER.debug(f"User Input: {user_input}")
        if user_input.lower() in ["exit", "quit"]:
            LOGGER.info("Exiting the agent.")
            break
        response = agent.ReAct_loop(user_input)
        LOGGER.info(f"Agent Response: {response}")


if __name__ == "__main__":
    main()
