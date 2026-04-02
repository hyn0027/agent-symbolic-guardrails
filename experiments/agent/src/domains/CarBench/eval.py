# Some of the eval code is adapted from the original evaluation code provided by the authors of MedAgentBench
# reference: https://github.com/stanfordmlgroup/MedAgentBench

from typing import List, Dict, Optional

import json
from datetime import datetime, timedelta

from config.logger import LOGGER
from config.loader import CONFIG

from agent import ReActAgent
from user import UserSimulator
from eval import TerminateReason

from .task import Task

eval_config = CONFIG.EVAL


def evaluate_single(
    terminate_reason: TerminateReason,
    agent: ReActAgent,
    user: UserSimulator,
    task: Task,
):
    LOGGER.info("=========== Evaluating Single Simulation ===========")
    LOGGER.info(f"Evaluating simulation with terminate reason: {terminate_reason}")
    LOGGER.info("Evaluate Single Not Implemented Yet.")


def aggregate_evals(res_list: List) -> None:
    LOGGER.info("=========== Aggregating Evaluation Results ===========")
    LOGGER.info("Aggregate Evals Not Implemented Yet.")
