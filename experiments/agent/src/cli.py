import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from agent import ReActAgent
from user import UserSimulator
from typing import Any
from eval import TerminateReason

from config.loader import CONFIG, args
from config.logger import LOGGER

from domains import BaseTask

if CONFIG.DATASET.NAME == "tau2":
    from domains.tau2.prompts import system_prompt, user_prompt, assess_end_conversation
    from domains.tau2.task import load_tasks
    from domains.tau2.eval import evaluate_single, aggregate_evals
elif CONFIG.DATASET.NAME == "MedAgentBench":
    from domains.MedAgentBench.prompts import (
        system_prompt,
        user_prompt,
        assess_end_conversation,
    )
    from domains.MedAgentBench.task import load_tasks
    from domains.MedAgentBench.eval import evaluate_single, aggregate_evals
elif CONFIG.DATASET.NAME == "CarBench":
    from domains.CarBench.prompts import (
        system_prompt,
        user_prompt,
        assess_end_conversation,
    )
    from domains.CarBench.task import load_tasks
    from domains.CarBench.eval import evaluate_single, aggregate_evals


def human_interaction() -> None:
    LOGGER.debug(f"Configuration Loaded: {CONFIG}")
    agent = ReActAgent(system_prompt=system_prompt())
    if CONFIG.AGENT.AGENT_INITIAL_MESSAGE:
        agent_message = agent.initiate_conversation()
        LOGGER.info(f"Agent: {agent_message}")
    try:
        while True:
            user_input = input("User: ")
            LOGGER.debug(f"User: {user_input}")
            if assess_end_conversation(user_input, agent):
                LOGGER.info("Exiting the agent.")
                agent.append_user_message(user_input)
                break
            response = agent.ReAct_loop(user_input)
            LOGGER.info(f"Agent: {response}")
            if assess_end_conversation(response, agent) or agent.end_conversation:
                LOGGER.info(f"Conversation ended by agent response.")
                break
    except KeyboardInterrupt:
        LOGGER.info("Exiting the agent due to keyboard interrupt.")
    finally:
        LOGGER.info("TOOL ERROR STATISTICS:")
        tool_error_stats = agent.report_tool_error_statistics()
        LOGGER.info(json.dumps(tool_error_stats, indent=2))
        agent.log_history()
        agent.shutdown()


def _run_once(user_task: BaseTask):
    agent = ReActAgent(
        system_prompt=system_prompt(user_task), task_arg=user_task.task_arg()
    )
    user = UserSimulator(system_prompt=user_prompt(user_task))
    if CONFIG.AGENT.AGENT_INITIAL_MESSAGE:
        agent_message = agent.initiate_conversation()
        LOGGER.info(f"Agent: {agent_message}")
    step_cnt = 0
    terminate_reason = None
    eval_res = None
    try:
        while True:
            step_cnt += 1

            assert isinstance(
                CONFIG.SIMULATION.MAX_STEPS, int
            ), "MAX_STEPS should be an integer."

            if step_cnt > CONFIG.SIMULATION.MAX_STEPS:
                LOGGER.info(
                    f"Simulation ended due to reaching max steps: {CONFIG.SIMULATION.MAX_STEPS}."
                )
                terminate_reason = TerminateReason.MAX_STEPS
                break
            user_input = user.respond_to_customer_support(agent_message)
            LOGGER.info(f"User: (round {step_cnt}) {user_input}")
            if assess_end_conversation(user_input, agent):
                LOGGER.info(f"Simulation ended due to user response.")
                terminate_reason = TerminateReason.USER_STOP
                agent.append_user_message(user_input)
                break
            agent_message = agent.ReAct_loop(user_input)
            LOGGER.info(f"Agent: {agent_message}")
            if assess_end_conversation(agent_message, agent) or agent.end_conversation:
                LOGGER.info(f"Simulation ended due to agent response.")
                terminate_reason = TerminateReason.AGENT_STOP
                break
        eval_res = evaluate_single(terminate_reason, agent, user, user_task)
    except KeyboardInterrupt:
        LOGGER.info("Exiting the agent due to keyboard interrupt.")
    finally:
        agent.shutdown()
    return eval_res


def run_random_task() -> None:
    LOGGER.debug(f"Configuration Loaded: {CONFIG}")

    import random

    tasks = load_tasks()
    random_task = random.choice(tasks)
    LOGGER.info(f"Selected Task:\n{random_task}")
    LOGGER.info(f"{'*' * 20} Starting Simulation {'*' * 20}")
    _run_once(random_task)


def run_given_task() -> None:
    if args.task_id is None:
        raise ValueError("Please provide a task ID using --task_id argument.")

    LOGGER.debug(f"Configuration Loaded: {CONFIG}")
    tasks = load_tasks()
    task_id = args.task_id
    LOGGER.info(f"Looking for Task ID: {task_id}")
    task = tasks[task_id]
    LOGGER.info(f"Selected Task:\n{task}")
    LOGGER.info(f"{'*' * 20} Starting Simulation {'*' * 20}")
    _run_once(task)


def run_dataset() -> None:
    LOGGER.debug(f"Configuration Loaded: {CONFIG}")

    tasks = load_tasks()
    LOGGER.info(f"Total tasks loaded: {len(tasks)}")
    eval_res_list = []
    # for idx, task in enumerate(tasks):
    #     LOGGER.info(f"{'=' * 10} Starting Running Task {idx + 1} {'=' * 10}")
    #     eval_res = _run_once(task)
    #     eval_res_list.append(eval_res)
    # aggregate_evals(eval_res_list)

    assert (
        isinstance(CONFIG.SIMULATION.MAX_WORKERS, int)
        and CONFIG.SIMULATION.MAX_WORKERS > 0
    ), "MAX_WORKERS should be a positive integer."

    with ThreadPoolExecutor(max_workers=CONFIG.SIMULATION.MAX_WORKERS) as executor:
        future_to_task = [executor.submit(_run_once, task) for task in tasks]
        for future in as_completed(future_to_task):
            eval_res = future.result()
            eval_res_list.append(eval_res)

    aggregate_evals(eval_res_list)
