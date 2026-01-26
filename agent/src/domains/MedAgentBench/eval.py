from typing import List
from agent import ReActAgent
from user import UserSimulator
from eval import TerminateReason
from config.logger import LOGGER
from config.loader import CONFIG

eval_config = CONFIG.EVAL


def evaluate_single(
    terminate_reason: TerminateReason,
    agent: ReActAgent,
    user: UserSimulator,
    task,
):
    LOGGER.info(f"Evaluating simulation with terminate reason: {terminate_reason}")
    return None


def aggregate_evals(res_list: List) -> None:
    LOGGER.info("Aggregating evaluation results...")
    return None
