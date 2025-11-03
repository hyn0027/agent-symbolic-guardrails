from agent import ReActAgent
from user import UserSimulator
from tasks.task import load_tasks_from_json_file
from config.loader import CONFIG
from config.logger import LOGGER


def human_interaction():
    LOGGER.debug(f"Configuration Loaded: {CONFIG}")
    agent = ReActAgent()
    initial_message = agent.initiate_conversation()
    LOGGER.info(f"Agent: {initial_message}")
    try:
        while True:
            user_input = input("User: ")
            LOGGER.debug(f"User: {user_input}")
            if user_input.lower() in ["exit", "quit"]:
                LOGGER.info("Exiting the agent.")
                break
            response = agent.ReAct_loop(user_input)
            LOGGER.info(f"Agent: {response}")
    except KeyboardInterrupt:
        LOGGER.info("Exiting the agent due to keyboard interrupt.")
    finally:
        agent.shutdown()


def _simulation_once(user_task: str):
    LOGGER.debug(f"Configuration Loaded: {CONFIG}")
    agent = ReActAgent()
    user = UserSimulator(user_task)
    agent_message = agent.initiate_conversation()
    LOGGER.info(f"Agent: {agent_message}")
    try:
        while True:
            user_input = user.respond_to_customer_support(agent_message)
            LOGGER.info(f"User: {user_input}")
            if "###STOP###" in user_input or "###TRANSFER###" in user_input or "###OUT-OF-SCOPE###" in user_input:
                LOGGER.info(f"Simulation ended due to token in user response.")
                break
            agent_message = agent.ReAct_loop(user_input)
            LOGGER.info(f"Agent: {agent_message}")
    except KeyboardInterrupt:
        LOGGER.info("Exiting the agent due to keyboard interrupt.")
    finally:
        agent.shutdown()


def user_simulation():
    import random
    
    tasks = load_tasks_from_json_file(CONFIG.SIMULATION.TASK_FILE)
    random_task = random.choice(tasks)
    LOGGER.info(f"Selected Task:\n{random_task}")
    _simulation_once(random_task.user_scenario)
