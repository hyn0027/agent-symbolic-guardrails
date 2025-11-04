# modified from tau bench code

from enum import Enum
from openai import OpenAI
from typing import Annotated, Optional, Dict, List
from pydantic import BaseModel, Field
from agent import ReActAgent
from user import UserSimulator
from .task import Task, RewardType, Action, ToolCall
from config.logger import LOGGER
import json


class TerminateReason(Enum):
    USER_STOP = "USER_STOP"
    MAX_STEPS = "MAX_STEPS"


class RewardInfo(BaseModel):
    """
    The reward received by the agent.
    """

    reward: Annotated[float, Field(description="The reward received by the agent.")]
    reward_breakdown: Annotated[
        Optional[dict[RewardType, float]],
        Field(
            description="The breakdown of the reward.",
            default=None,
        ),
    ]
    info: Annotated[
        Optional[dict],
        Field(description="Additional information about the reward.", default=None),
    ]


class ActionEvaluator:
    @classmethod
    def calculate_reward(
        cls,
        task: Task,
        tool_call_history: List[Dict],
    ) -> RewardInfo:
        """
        Calculate the reward based on whether the agent communicated the required information.
        """
        if task.evaluation_criteria is None:
            return RewardInfo(
                reward=1.0,
                info={"note": "No evaluation criteria"},
                reward_breakdown={RewardType.ACTION: 1.0},
            )
        golden_actions = task.evaluation_criteria.actions
        if not golden_actions:
            return RewardInfo(
                reward=1.0,
                info={"note": "No actions to evaluate"},
                reward_breakdown={RewardType.ACTION: 1.0},
            )

        action_match_list = cls.evaluate_actions(tool_call_history, golden_actions)

        all_expectations_met = all(action_match for action_match in action_match_list)
        reward = 1.0 if all_expectations_met else 0.0

        return RewardInfo(
            reward=reward,
            reward_breakdown={RewardType.ACTION: reward},
            info={"detailed_results": action_match_list},
        )

    @classmethod
    def dict2Toolcall(cls, tc_dict: Dict) -> ToolCall:
        return ToolCall(
            id=tc_dict["id"],
            name=tc_dict["function"]["name"],
            arguments=json.loads(tc_dict["function"]["arguments"]),
        )

    @classmethod
    def evaluate_actions(
        cls,
        tool_call_history: List[Dict],
        golden_actions: list[Action],
    ) -> list[bool]:
        if len(golden_actions) == 0:
            return []

        action_match_list = []
        predicted_tool_calls: list[ToolCall] = []
        for tc in tool_call_history:
            predicted_tool_calls.extend(cls.dict2Toolcall(tc) for tc in [tc])

        # Check if all the gold actions are in the predicted actions
        for gold_action in golden_actions:
            gold_action_match = False
            for pred_tool_call in predicted_tool_calls:
                if gold_action.compare_with_tool_call(pred_tool_call):
                    gold_action_match = True
                    LOGGER.debug(
                        f"Gold action matched: {gold_action} with predicted tool call: {pred_tool_call}"
                    )
                    break
            if not gold_action_match:
                LOGGER.debug(f"Gold action NOT matched: {gold_action}")
            action_match_list.append(gold_action_match)
        return action_match_list


class CommunicateEvaluator:
    """
    Evaluates whether or not the agent communicated the required information.
    """

    @classmethod
    def calculate_reward(
        cls,
        task: Task,
        full_trajectory: list[Dict],
    ) -> RewardInfo:
        """
        Calculate the reward based on whether the agent communicated the required information.
        """
        if task.evaluation_criteria is None:
            return RewardInfo(
                reward=1.0,
                info={"notes": "No evaluation criteria"},
                reward_breakdown={RewardType.COMMUNICATE: 1.0},
            )
        communicate_info = task.evaluation_criteria.communicate_info
        if not communicate_info:
            return RewardInfo(
                reward=1.0,
                info={"note": "No communicate_info to evaluate"},
                reward_breakdown={RewardType.COMMUNICATE: 1.0},
            )

        results = cls.evaluate_communicate_info(full_trajectory, communicate_info)

        # Calculate reward: 1 if all expectations are met, 0 otherwise
        all_expectations_met = all(res for res in results)
        reward = 1.0 if all_expectations_met else 0.0

        return RewardInfo(
            reward=reward,
            reward_breakdown={RewardType.COMMUNICATE: reward},
            info={"detailed_results": results},
        )

    @classmethod
    def evaluate_communicate_info(
        cls,
        full_trajectory: list[Dict],
        communicate_info: list[str],
    ) -> list[bool]:
        """
        Evaluate whether the agent communicates the information correctly.
        """
        if len(communicate_info) == 0:
            return []

        outputs = []
        for info_str in communicate_info:
            found = False
            for message in full_trajectory:
                if message["role"] != "assistant":
                    continue
                if "content" not in message or message["content"] is None:
                    continue
                if info_str.lower() in message["content"].lower().replace(
                    ",", ""
                ):  # TODO: This could be improved!
                    found = True
                    LOGGER.debug(
                        f"Communicate info '{info_str}' found in message: {message['content']}"
                    )
                    break
            if not found:
                LOGGER.debug(f"Communicate info '{info_str}' NOT found in trajectory.")
            outputs.append(found)
        return outputs


class NLAssertionsEvaluator:
    """
    Judge that evaluates whether a trajectory adheres to all the natural-language assertions.
    """

    @classmethod
    def calculate_reward(
        cls,
        task: Task,
        full_trajectory: list[Dict],
    ) -> RewardInfo:
        """
        Calculate the reward for the simulation by using an LLM to evaluate whether the trajectory adheres to all the natural-language assertions
        """
        if task.evaluation_criteria is None:
            return RewardInfo(
                reward=1.0,
                info={"note": "No evaluation criteria"},
                reward_breakdown={RewardType.NL_ASSERTION: 1.0},
            )
        nl_assertions = task.evaluation_criteria.nl_assertions
        if not nl_assertions:
            return RewardInfo(
                reward=1.0,
                info={"note": "No nl_assertions to evaluate"},
                reward_breakdown={RewardType.NL_ASSERTION: 1.0},
            )

        results = cls.evaluate_nl_assertions(full_trajectory, nl_assertions)

        # Calculate reward: 1 if all expectations are met, 0 otherwise
        all_expectations_met = all(result for result in results)
        reward = 1.0 if all_expectations_met else 0.0

        return RewardInfo(
            reward=reward,
            reward_breakdown={RewardType.NL_ASSERTION: reward},
            info={"detailed_results": results},
        )

    @classmethod
    def evaluate_nl_assertions(
        cls,
        trajectory: list[Dict],
        nl_assertions: list[str],
    ) -> list[bool]:
        trajectory_str = json.dumps(trajectory, indent=2)
        # System prompt similar to the TypeScript implementation
        system_prompt = """
        TASK
        - You will be given a list of expected outcomes and a conversation that was collected during a test case run.
        - The conversation is between an agent and a customer.
        - Your job is to evaluate whether the agent satisfies each of the expected outcomes.
        - Grade each expected outcome individually.

        FORMAT
        - Your response should be a JSON object with the following fields:
        - `reasoning`: a short explanation for your classification
        - `metExpectation`: `true` if the agent satisfies the expected outcomes, `false` otherwise
        - `expectedOutcome`: repeat the expectation from the input that you are grading
        
        Example response structure:
        {
            "results": [
                {
                    "expectedOutcome": "<one of the expected outcomes from the input>",
                    "reasoning": "<reasoning trace>",
                    "metExpectation": <false or true>,
                },
                ...
            ]
        }
        """

        user_prompt = f"""
        conversation:
        {trajectory_str}
        
        expectedOutcomes:
        {nl_assertions}
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        MAX_RETRIES = 5
        for attempt in range(MAX_RETRIES):
            try:
                assistant_message = cls._call_LLM(messages)
                if assistant_message.find("```json") != -1:
                    assistant_message = (
                        assistant_message.split("```json")[1].split("```")[0].strip()
                    )
                result_data = json.loads(assistant_message)
                LOGGER.debug(
                    f"NL Assertions Evaluation Results: {json.dumps(result_data, indent=2)}"
                )
                return [
                    result["metExpectation"]
                    for result in result_data.get("results", [])
                ]
            except Exception as e:
                LOGGER.error(
                    f"Error in NL Assertions evaluation LLM call or parsing response: {e}"
                )
                if attempt == MAX_RETRIES - 1:
                    LOGGER.error(
                        "Max retries reached. Failing the NL assertions evaluation."
                    )
                    return [False] * len(nl_assertions)
                LOGGER.info(
                    f"Retrying NL assertions evaluation (attempt {attempt + 1})..."
                )

    @classmethod
    def _call_LLM(
        cls,
        messages: list,
        model: str = "gpt-4o",
        temperature: float = 0.0,
    ) -> str:
        client = OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content


def evaluate_simulation(
    terminate_reason: TerminateReason,
    agent: ReActAgent,
    user: UserSimulator,
    task: Task,
):
    LOGGER.info(f"Evaluating simulation with terminate reason: {terminate_reason}")
    if terminate_reason == TerminateReason.MAX_STEPS:
        return RewardInfo(
            reward=0.0,
            info={
                "note": f"Simulation terminated prematurely. Termination reason: {terminate_reason.value}"
            },
        )

    action_reward_info = ActionEvaluator.calculate_reward(
        task, agent.fetch_tool_call_history() + user.fetch_tool_call_history()
    )
    communicate_reward_info = CommunicateEvaluator.calculate_reward(task, agent.history)
    nl_assertions_reward_info = NLAssertionsEvaluator.calculate_reward(
        task, agent.history
    )

    reward = 1.0
    reward_breakdown = {}

    if action_reward_info.reward_breakdown is not None:
        reward_breakdown.update(action_reward_info.reward_breakdown)
    reward *= action_reward_info.reward

    if communicate_reward_info.reward_breakdown is not None:
        reward_breakdown.update(communicate_reward_info.reward_breakdown)
    reward *= communicate_reward_info.reward

    if nl_assertions_reward_info.reward_breakdown is not None:
        reward_breakdown.update(nl_assertions_reward_info.reward_breakdown)
    reward *= nl_assertions_reward_info.reward

    return RewardInfo(
        reward=reward,
        reward_breakdown=reward_breakdown,
        info={
            "action_evaluation": action_reward_info.info,
            "communicate_evaluation": communicate_reward_info.info,
            "nl_assertions_evaluation": nl_assertions_reward_info.info,
        },
    )
