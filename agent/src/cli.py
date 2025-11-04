from agent import ReActAgent
from user import UserSimulator
import json
from tasks.tau2.task import load_tasks_from_json_file, Task
from tasks.tau2.eval import TerminateReason, evaluate_simulation
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


def _simulation_once(user_task: Task):
    agent = ReActAgent()
    user = UserSimulator(user_task.user_scenario)
    agent_message = agent.initiate_conversation()
    LOGGER.info(f"Agent: {agent_message}")
    step_cnt = 0
    terminate_reason = None
    eval_res = None
    try:
        while True:
            step_cnt += 1
            if step_cnt > CONFIG.SIMULATION.MAX_STEPS:
                LOGGER.info(
                    f"Simulation ended due to reaching max steps: {CONFIG.SIMULATION.MAX_STEPS}."
                )
                terminate_reason = TerminateReason.MAX_STEPS
                break
            user_input = user.respond_to_customer_support(agent_message)
            LOGGER.info(f"User: {user_input}")
            if (
                "###STOP###" in user_input
                or "###TRANSFER###" in user_input
                or "###OUT-OF-SCOPE###" in user_input
            ):
                LOGGER.info(f"Simulation ended due to token in user response.")
                terminate_reason = TerminateReason.USER_STOP
                break
            agent_message = agent.ReAct_loop(user_input)
            LOGGER.info(f"Agent: {agent_message}")
        eval_res = evaluate_simulation(terminate_reason, agent, user, user_task)
        LOGGER.info(f"Reward: {eval_res.reward}")
        LOGGER.info(
            f"Reward Breakdown: {json.dumps(eval_res.reward_breakdown, indent=2)}"
        )
    except KeyboardInterrupt:
        LOGGER.info("Exiting the agent due to keyboard interrupt.")
    finally:
        agent.shutdown()
    return eval_res


def user_simulation():
    LOGGER.debug(f"Configuration Loaded: {CONFIG}")

    import random

    tasks = load_tasks_from_json_file(CONFIG.SIMULATION.TASK_FILE)
    random_task = random.choice(tasks)
    LOGGER.info(f"Selected Task:\n{random_task}")
    LOGGER.info(f"{'*' * 20} Starting Simulation {'*' * 20}")
    _simulation_once(random_task)


def eval_full_dataset():
    LOGGER.debug(f"Configuration Loaded: {CONFIG}")

    tasks = load_tasks_from_json_file(CONFIG.SIMULATION.TASK_FILE)
    total_reward = 0.0
    total_reward_without_nl = 0.0
    for idx, task in enumerate(tasks):
        LOGGER.info(f"{'=' * 10} Starting Simulation for Task {idx + 1} {'=' * 10}")
        eval_res = _simulation_once(task)
        if eval_res:
            total_reward += eval_res.reward
            total_reward_without_nl += eval_res.info["reward_without_nl"]
    avg_reward = total_reward / len(tasks) if tasks else 0.0
    avg_reward_without_nl = total_reward_without_nl / len(tasks) if tasks else 0.0
    LOGGER.info(f"Average Reward over {len(tasks)} tasks: {avg_reward}")
    LOGGER.info(
        f"Average Reward without NL component over {len(tasks)} tasks: {avg_reward_without_nl}"
    )
