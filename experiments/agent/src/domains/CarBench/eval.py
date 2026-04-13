# Some of the eval code is adapted from the original evaluation code provided by the authors of MedAgentBench
# reference: https://github.com/stanfordmlgroup/MedAgentBench

from typing import List, Any, Dict, Tuple, Optional, Union, Set
from config.logger import LOGGER
from config.loader import CONFIG
import asyncio
import json

from agent import ReActAgent
from mcp_client import MCPClient
from user import UserSimulator
from eval import TerminateReason
from hashlib import sha256

from .task import Task, TaskType
from .context.dynamic_context_state import context_state, ContextState
from .context import load_context
from .policy_evaluator import (
    load_policy_evaluator,
    policy_errors_during_runtime,
    BasePolicyEvaluatorEnv,
)

eval_config = CONFIG.EVAL

Hashable = Union[str, int, float, Tuple["Hashable"], Tuple[Tuple[str, "Hashable"]]]
ToHashable = Union[
    str, int, float, Dict[str, "ToHashable"], List["ToHashable"], Set["ToHashable"]
]
USER_AS_A_TOOL_ACTION_NAMES = [
    "respond",
    "message_to_user",
    "clarify_with_user_request_of_invalid_tool_arguments",
    "clarify_with_user_request_of_unavailable_tools",
    "disambiguate_with_user_suitable_tool_results",
    "disambiguate_with_user_suitable_tools",
    "disambiguate_with_user_tool_arguments",
    "ask_user_for_confirmation",
]
RESPOND_ACTION_NAME = "respond"
RESPOND_ACTION_FIELD_NAME = "content"


def consistent_hash(
    value: Hashable,
) -> str:
    return sha256(str(value).encode("utf-8")).hexdigest()


def to_hashable(item: ToHashable) -> Hashable:
    if isinstance(item, dict):
        return tuple((key, to_hashable(value)) for key, value in sorted(item.items()))
    elif isinstance(item, list):
        return tuple(to_hashable(element) for element in item)
    elif isinstance(item, set):
        return tuple(sorted(to_hashable(element) for element in item))
    else:
        return item


def evaluate_single(
    terminate_reason: TerminateReason,
    agent: ReActAgent,
    user: UserSimulator,
    task: Task,
):
    LOGGER.info("=========== Evaluating Single Simulation ===========")
    LOGGER.info(f"Evaluating simulation with terminate reason: {terminate_reason}")

    def eval_original_bench() -> Any:
        load_context(task)
        tool_policy_error_during_runtime = agent.call_mcp_tool_without_recording(
            "get_policy_errors_during_runtime", {}
        )
        policy_errors_during_runtime.set(tool_policy_error_during_runtime)

        def is_hallucination_task(task_type: TaskType) -> bool:
            """Check if the task is a hallucination task type."""
            return task_type in [
                TaskType.HALLUCINATION_MISSING_TOOL,
                TaskType.HALLUCINATION_MISSING_TOOL_PARAMETER,
                TaskType.HALLUCINATION_MISSING_TOOL_RESPONSE,
            ]

        def calculate_state_based_reward(
            state_hashes: List[str],
        ) -> Tuple[Optional[bool], Optional[bool], Optional[bool], float]:
            if is_hallucination_task(task.task_type):
                return None, None, None, 0.0

            context_state_hash = agent.call_mcp_tool_without_recording(
                "get_current_state_hash", {}
            )

            new_mcp_client = MCPClient(
                eval_config.MCP_SERVER_COMMAND,
                eval_config.MCP_SERVER_COMMAND_EVAL_ARGS,
                agent.task_arg,
            )
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(new_mcp_client.initialize())

            def _shutdown_new_loop() -> None:
                try:
                    pending = asyncio.all_tasks(loop=new_loop)
                    for task in pending:
                        task.cancel()
                    new_loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
                    new_loop.run_until_complete(new_loop.shutdown_asyncgens())
                finally:
                    new_loop.close()

            def call_tool_with_new_client(name: str, args: Dict) -> Dict:
                if name in USER_AS_A_TOOL_ACTION_NAMES:
                    LOGGER.warning(
                        f"Tool {name} is a user-as-a-tool action, skipping call with new client."
                    )
                    return {}
                try:
                    return new_loop.run_until_complete(
                        new_mcp_client.call_tool_without_recording(name, args)
                    )
                except Exception as e:
                    LOGGER.error(f"Error calling tool {name} with new client: {str(e)}")
                    return {}

            # Record initial state hash for ground truth
            # gt_state_hashes = [call_tool_with_new_client("get_current_state_hash", {})]

            for action in task.actions:
                call_tool_with_new_client(action.name, action.kwargs)

            gt_state_hashes = call_tool_with_new_client("get_all_state_hashes", {}).get(
                "result", []
            )

            # print(f"GT state hashes: {gt_state_hashes}")
            # print(f"Actual state hashes: {state_hashes}")

            # Check final state correctness
            r_actions_final = (
                context_state_hash == gt_state_hashes[-1] if gt_state_hashes else False
            )
            reward_delta = 0.0 if not r_actions_final else 0.0

            # Check intermediate states correctness
            gt_state_hashes_set = set(gt_state_hashes)
            actual_state_hashes_set = set(state_hashes)
            r_actions_intermediate = actual_state_hashes_set.issubset(
                gt_state_hashes_set
            )
            if not r_actions_intermediate:
                reward_delta = -1.0

            if not r_actions_final:
                reward_delta = -1.0

            # Legacy field for backward compatibility
            r_actions = r_actions_final and r_actions_intermediate

            _shutdown_new_loop()

            return r_actions_final, r_actions_intermediate, r_actions, reward_delta

        def calculate_tool_subset_reward(
            performed_actions: List,
        ) -> Tuple[Optional[float], Optional[List[str]], float]:
            """
            Calculate tool subset reward (coverage of required information-gathering tools).

            Args:
                task: The task being evaluated
                performed_actions: List of actions performed by the agent

            Returns:
                Tuple of (r_tool_subset, tool_subset_missing_tools, reward_delta)
            """
            if is_hallucination_task(task.task_type):
                return None, None, 0.0

            gt_action_names = {
                action.name
                for action in task.actions
                if action.name != RESPOND_ACTION_NAME
            }
            performed_action_names = {action["name"] for action in performed_actions}

            # Calculate missing tools from ground truth
            tool_subset_missing_tools = list(gt_action_names - performed_action_names)
            r_tool_subset = gt_action_names.issubset(performed_action_names)

            if not r_tool_subset:
                return 0.0, tool_subset_missing_tools, -1.0
            else:
                return 1.0, tool_subset_missing_tools, 0.0

        def calculate_tool_execution_reward(
            score_tool_execution_errors: bool,
        ) -> Tuple[float, List, float]:
            """
            Calculate tool execution error reward.

            Args:
                score_tool_execution_errors: Whether to score tool execution errors

            Returns:
                Tuple of (r_tool_execution, tool_execution_errors, reward_delta)
            """
            tool_execution_errors = agent.call_mcp_tool_without_recording(
                "get_tool_execution_errors_during_runtime", {}
            )

            if score_tool_execution_errors and len(tool_execution_errors) > 0:
                return 0.0, tool_execution_errors, -1.0
            else:
                return 1.0, tool_execution_errors, 0.0

        def calculate_end_conversation_reward() -> Tuple[float, Optional[str], float]:
            """
            Calculate end conversation reward (user satisfaction).

            Returns:
                Tuple of (r_user_end_conversation, end_conversation_keyword, reward_delta)
            """
            end_conversation_fail = agent.end_conversation_falure

            if len(end_conversation_fail) > 0:
                end_conversation_keyword = end_conversation_fail[0][
                    "conversation_control_keyword"
                ]
                return 0.0, end_conversation_keyword, -1.0
            else:
                return 1.0, None, 0.0

        def calculate_output_reward() -> Tuple[Optional[float], Dict]:
            """
            Calculate output-string-based reward.

            Returns:
                Tuple of (r_outputs, outputs)
            """
            # Placeholder for future implementation
            return None, {}

        def filter_trajectory_messages(messages: List[Dict]) -> List[Dict]:
            """
            Filter trajectory messages to include only specified keys.

            Args:
                messages: List of conversation messages

            Returns:
                Filtered list of messages with core fields only
            """
            traj_messages = (
                messages[1:] if messages[0]["role"] == "system" else messages
            )
            traj_messages_core = []

            for msg in traj_messages:
                filtered_msg = {}
                for key in ["role", "content", "name", "tool_calls"]:
                    if key in msg:
                        if (
                            key == "content"
                            and "tool_calls" in msg
                            and msg["tool_calls"]
                        ):
                            filtered_msg[key] = ""
                        else:
                            filtered_msg[key] = msg[key]
                traj_messages_core.append(filtered_msg)

            return traj_messages_core

        def enhance_policy_line_with_context(
            line: str,
            performed_action_names: Set[str],
            difference_is_more_than_3_degrees: bool,
        ) -> Optional[str]:
            """
            Enhance policy line with context-specific information or skip if not applicable.

            Args:
                line: Policy line to enhance
                performed_action_names: Set of action names performed by agent
                difference_is_more_than_3_degrees: Whether temperature difference exceeds 3 degrees

            Returns:
                Enhanced policy line or None if policy should be skipped
            """
            if "REQUIRES_CONFIRMATION" in line:
                if (
                    len(
                        performed_action_names.intersection(
                            {
                                "send_email",
                                "open_close_trunk_door",
                                "set_head_lights_high_beams",
                            }
                        )
                    )
                    > 0
                ):
                    return (
                        line
                        + " The tools that require confirmation are: 'send_email', 'open_close_trunk_door', and 'set_head_lights_high_beams'."
                    )
                return None

            elif (
                "windows are requested by the user to open more than 25% (absolute position) and AC is ON in that moment"
                in line
            ):
                if len(performed_action_names.intersection({"open_close_window"})) > 0:
                    return (
                        line
                        + " Consider that you can only know the AC status if it was turned on **before** the user request to open the windows. Mark not applicable, if th AC was not requested to turn on before, also  mark not applicable if the windows are closed or requested to close. Also this policy is one-way: applies only if user requests to open the windows, turn on AC request are handled in another policy."
                    )
                return None

            elif "In certain weather conditions, the vehicle control actions" in line:
                if (
                    len(
                        performed_action_names.intersection(
                            {"open_close_sunroof", "set_fog_lights"}
                        )
                    )
                    == 0
                ):
                    return None

            elif "user sets the temperature to a single seat zone" in line:
                if (
                    len(
                        performed_action_names.intersection({"set_climate_temperature"})
                    )
                    == 0
                    or not difference_is_more_than_3_degrees
                ):
                    return None

            elif (
                "route is presented in detail (fastest route, shortest route, or upon user detail request)"
                in line
            ):
                if (
                    len(
                        performed_action_names.intersection(
                            {"get_routes_from_start_to_destination"}
                        )
                    )
                    > 0
                ):
                    return (
                        line
                        + " For this policy, first reason which routes were presented in detail, then evaluate if these routes include a toll road - if true this would be included in the list of road types else it's not present, then evaluate the policy for the routes identified to be presented in detail."
                    )
                return None

            elif (
                "user asks for a multi-stop route and does not specify the route selection"
                in line
            ):
                if (
                    len(
                        performed_action_names.intersection(
                            {"get_routes_from_start_to_destination"}
                        )
                    )
                    == 0
                ):
                    return None

            return line

        def calculate_policy_llm_errors(
            policy_evaluator,
            messages: List[Dict],
            performed_action_names: Set[str],
            difference_is_more_than_3_degrees: bool,
        ) -> List[str]:
            """
            Calculate LLM-based policy errors.

            Args:
                policy_evaluator: Policy evaluator instance
                messages: Conversation messages
                performed_action_names: Set of action names performed
                difference_is_more_than_3_degrees: Whether temperature difference exceeds 3 degrees

            Returns:
                List of policy error reasoning strings
            """

            from .wiki import WIKI_LLM_POL_LINES

            traj_messages_core = filter_trajectory_messages(messages)
            pol_llm_evaluation_results = []

            for line in WIKI_LLM_POL_LINES:
                enhanced_line = enhance_policy_line_with_context(
                    line, performed_action_names, difference_is_more_than_3_degrees
                )

                if enhanced_line is None:
                    continue

                evaluation_result = policy_evaluator.evaluate_llm(
                    policy=enhanced_line, trajectory=str(traj_messages_core)
                )
                pol_llm_evaluation_results.append(json.loads(evaluation_result))

            policy_llm_errors = [
                eval_result["reasoning"]
                for eval_result in pol_llm_evaluation_results
                if not eval_result["policy_followed"]
            ]

            return policy_llm_errors

        def calculate_policy_reward(
            evaluate_policy: bool,
            score_policy_errors: bool,
            policy_evaluator: BasePolicyEvaluatorEnv,
            messages: List[Dict],
            performed_action_names: Set[str],
            difference_is_more_than_3_degrees: bool,
        ) -> Tuple[Optional[float], List[str], List, float]:
            """
            Calculate policy compliance reward (LLM-based and AUT-based).

            Args:
                evaluate_policy: Whether to evaluate policy compliance
                score_policy_errors: Whether to score policy errors
                policy_evaluator: Policy evaluator instance
                messages: Conversation messages
                performed_action_names: Set of action names performed
                difference_is_more_than_3_degrees: Whether temperature difference exceeds 3 degrees

            Returns:
                Tuple of (r_policy, policy_llm_errors, policy_errors_aut, reward_delta)
            """
            if is_hallucination_task(task.task_type):
                return None, None, None, 0.0

            policy_llm_errors = []
            policy_errors_aut = []
            r_policy = None
            reward_delta = 0.0

            # LLM-based Policy Error Calculation
            if evaluate_policy:
                r_policy = 1.0
                policy_llm_errors = calculate_policy_llm_errors(
                    policy_evaluator,
                    messages,
                    performed_action_names,
                    difference_is_more_than_3_degrees,
                )
            else:
                r_policy = None

            # AUT-based Policy Error Calculation
            if evaluate_policy:
                traj_messages = (
                    messages[1:] if messages[0]["role"] == "system" else messages
                )
                policy_evaluator.evaluate_aut(trajectory=traj_messages)
                policy_errors_aut = policy_errors_during_runtime.get()

            # Calculate reward penalty
            if score_policy_errors and (
                len(policy_errors_aut) > 0 or len(policy_llm_errors) > 0
            ):
                r_policy = 0.0
                reward_delta = -1.0

            return r_policy, policy_llm_errors, policy_errors_aut, reward_delta

        reward = 1.0
        performed_actions = agent.fetch_successful_tool_call_history()

        # Get temperature difference for policy evaluation
        climate_temperature_driver = context_state.get().climate_temperature_driver
        climate_temperature_passenger = (
            context_state.get().climate_temperature_passenger
        )
        difference_is_more_than_3_degrees = (
            abs(climate_temperature_driver - climate_temperature_passenger) > 3
        )

        # Get performed action names for policy evaluation
        performed_action_names = {action["name"] for action in performed_actions}

        # ==== State-based Reward ====
        (
            r_actions_final,
            r_actions_intermediate,
            r_actions,
            reward_delta,
        ) = calculate_state_based_reward(
            state_hashes=agent.call_mcp_tool_without_recording(
                "get_all_state_hashes", {}
            ),
        )
        reward += reward_delta

        # print(r_actions_final, r_actions_intermediate, r_actions, reward_delta)

        # ==== Tool Subset Evaluation Reward ====
        r_tool_subset, tool_subset_missing_tools, reward_delta = (
            calculate_tool_subset_reward(performed_actions=performed_actions)
        )
        reward += reward_delta

        # ==== Tool-Execution-Error-Calculations ====
        r_tool_execution, tool_execution_errors, reward_delta = (
            calculate_tool_execution_reward(
                score_tool_execution_errors=eval_config.SCORE_TOOL_EXECUTION_ERRORS,
            )
        )

        reward += reward_delta

        # ==== End-Conversation-Failure-Calculations ====
        r_user_end_conversation, end_conversation_keyword, reward_delta = (
            calculate_end_conversation_reward()
        )
        reward += reward_delta

        # ==== Output-string-based Reward ====
        r_outputs, outputs = calculate_output_reward()

        # ==== Policy-Error-Calculations ====
        r_policy, policy_llm_errors, policy_errors_aut, reward_delta = (
            calculate_policy_reward(
                evaluate_policy=eval_config.EVALUATE_POLICY,
                score_policy_errors=eval_config.SCORE_POLICY_ERRORS,
                policy_evaluator=load_policy_evaluator(
                    policy_evaluator_strategy=eval_config.POLICY_EVALUATOR_STRATEGY,
                    model=eval_config.POLICY_EVALUATOR_MODEL,
                    provider=eval_config.POLICY_EVALUATOR_PROVIDER,
                ),
                messages=agent.history,
                performed_action_names=performed_action_names,
                difference_is_more_than_3_degrees=difference_is_more_than_3_degrees,
            )
        )
        reward += reward_delta

        # Ensure reward doesn't go below 0
        reward = max(0.0, reward)

        return
        # TODO

        info = RewardInfo(
            r_actions=r_actions,
            r_actions_final=r_actions_final,
            r_actions_intermediate=r_actions_intermediate,
            r_tool_subset=r_tool_subset,
            tool_subset_missing_tools=tool_subset_missing_tools,
            r_tool_execution=r_tool_execution,
            tool_execution_errors=tool_execution_errors,
            r_policy=r_policy,
            policy_llm_errors=policy_llm_errors,
            policy_aut_errors=policy_errors_aut,
            r_user_end_conversation=r_user_end_conversation,
            end_conversation_keyword=end_conversation_keyword,
            r_outputs=r_outputs,
            outputs=outputs,
        )
        return RewardResult(reward=reward, info=info, actions=performed_actions)

    eval_original_bench()


def aggregate_evals(res_list: List) -> None:
    LOGGER.info("=========== Aggregating Evaluation Results ===========")
    LOGGER.info("Aggregate Evals Not Implemented Yet.")
