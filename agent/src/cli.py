from agent import ReActAgent
from user import UserSimulator
from typing import Any
from eval import TerminateReason
import argparse
import json

from config.loader import CONFIG
from config.logger import LOGGER

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


total_tool_error_statistics = {
    "raise_count_with_type": {},
    "error_calling_log": [],
    "count_with_error_log": 0,
    "count_without_error_log": 0,
}


def report_total_tool_error_statistics() -> None:
    LOGGER.info("TOTAL TOOL ERROR STATISTICS:")
    LOGGER.info(json.dumps(total_tool_error_statistics, indent=2))


def _add_tool_error_statistics(tool_error_stats: dict):
    for err_type_key, count in tool_error_stats.get(
        "raise_count_with_type", {}
    ).items():
        if err_type_key not in total_tool_error_statistics["raise_count_with_type"]:
            total_tool_error_statistics["raise_count_with_type"][err_type_key] = 0
        total_tool_error_statistics["raise_count_with_type"][err_type_key] += count
    total_tool_error_statistics["error_calling_log"].extend(
        tool_error_stats.get("error_calling_log", [])
    )
    if len(tool_error_stats.get("error_calling_log", [])) > 0:
        total_tool_error_statistics["count_with_error_log"] += 1
    else:
        total_tool_error_statistics["count_without_error_log"] += 1


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
            if assess_end_conversation(user_input):
                LOGGER.info("Exiting the agent.")
                agent.append_user_message(user_input)
                break
            response = agent.ReAct_loop(user_input)
            LOGGER.info(f"Agent: {response}")
            if assess_end_conversation(agent_message) or agent.end_conversation:
                LOGGER.info(f"Conversation ended by agent response.")
                break
    except KeyboardInterrupt:
        LOGGER.info("Exiting the agent due to keyboard interrupt.")
    finally:
        LOGGER.info("TOOL ERROR STATISTICS:")
        tool_error_stats = agent.report_tool_error_statistics()
        _add_tool_error_statistics(tool_error_stats)
        LOGGER.info(json.dumps(tool_error_stats, indent=2))
        agent.shutdown()


def _run_once(user_task: Any):
    agent = ReActAgent(system_prompt=system_prompt())
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
            LOGGER.info(f"User: {user_input}")
            if assess_end_conversation(user_input):
                LOGGER.info(f"Simulation ended due to user response.")
                terminate_reason = TerminateReason.USER_STOP
                agent.append_user_message(user_input)
                break
            agent_message = agent.ReAct_loop(user_input)
            LOGGER.info(f"Agent: {agent_message}")
            if assess_end_conversation(agent_message) or agent.end_conversation:
                LOGGER.info(f"Simulation ended due to agent response.")
                terminate_reason = TerminateReason.AGENT_STOP
                break
        eval_res = evaluate_single(terminate_reason, agent, user, user_task)
    except KeyboardInterrupt:
        LOGGER.info("Exiting the agent due to keyboard interrupt.")
    finally:
        LOGGER.info("TOOL ERROR STATISTICS:")
        tool_error_stats = agent.report_tool_error_statistics()
        _add_tool_error_statistics(tool_error_stats)
        LOGGER.info(json.dumps(tool_error_stats, indent=2))
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
    parser = argparse.ArgumentParser(description="Run a specific task by ID.")
    parser.add_argument(
        "-id", "--task_id", type=int, required=True, help="ID of the task to run."
    )
    args = parser.parse_args()

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
    eval_res_list = []
    for idx, task in enumerate(tasks):
        LOGGER.info(f"{'=' * 10} Starting Running Task {idx + 1} {'=' * 10}")
        eval_res = _run_once(task)
        eval_res_list.append(eval_res)
    aggregate_evals(eval_res_list)
    report_total_tool_error_statistics()
