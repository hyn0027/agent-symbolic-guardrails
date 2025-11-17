from openai import OpenAI
import json
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from typing import Dict, List, Optional
import asyncio
from mcp_client import MCPClient
from config.loader import CONFIG
from config.logger import LOGGER

agent_config = CONFIG.AGENT
safeguard_config = CONFIG.SAFEGUARD


class ReActAgent:
    def __init__(self, system_prompt: str):
        self.model = agent_config.MODEL
        self.temperature = agent_config.TEMPERATURE
        self.system_prompt = system_prompt
        self._initialize()

    def _initialize(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        LOGGER.info("Initializing MCP Client")
        self.mcp_client = MCPClient(
            agent_config.MCP_SERVER_COMMAND, agent_config.MCP_SERVER_COMMAND_TEST_ARGS
        )
        self.loop.run_until_complete(self.mcp_client.initialize())

        LOGGER.debug("MCP TOOL")
        LOGGER.debug(self.mcp_client.tools)
        self.tools = self.mcp_client.list_OPENAI_tools()
        self.history = [
            {"role": "system", "content": self.system_prompt},
        ]
        LOGGER.info(f"Agent initialization complete. Detected {len(self.tools)} tools.")
        LOGGER.info("Available tools have been successfully enumerated.")
        # LOGGER.debug(json.dumps(self.tools, indent=2))

        self.remaining_tool_call = []
        self.tmp_user_response = ""
        self.override_assistant_msg = None
        self.end_conversation = False
        self.count_tool_call_fails = 0

        self.golden_eval_hist = []

    def initiate_conversation(self) -> str:
        self.history.append(
            {"role": "assistant", "content": agent_config.INITIAL_CONVERSTION}
        )
        return agent_config.INITIAL_CONVERSTION

    def append_user_message(self, message: str):
        self.history.append({"role": "user", "content": message})

    def _process_tool_call(
        self, tool_call, user_confirmed: bool, confirmation_msg: Optional[str] = None
    ) -> Optional[str]:
        tool_name = tool_call.function.name
        tool_args = tool_call.function.arguments
        tool_meta = self.mcp_client.get_tool_metadata(tool_name)

        if safeguard_config.USER_CONFIRMATION and not user_confirmed:
            if tool_meta.get("require_confirmation", False):
                LOGGER.info(
                    f"Tool '{tool_name}' requires user confirmation before invocation."
                )
                confirmation_message = (
                    safeguard_config.USER_CONFIRMATION_TEMPLATE.format(
                        tool_name=tool_name,
                        tool_args=(
                            json.dumps(tool_args)
                            if isinstance(tool_args, dict)
                            else str(tool_args)
                        ),
                    )
                )
                return confirmation_message
        if agent_config.TEST_WITH_GOLDEN and not tool_meta.get(
            "skip_golden_eval", False
        ):
            self.loop.run_until_complete(self.mcp_client.save_state())

        tool_response = self.loop.run_until_complete(
            self.mcp_client.call_tool(tool_name, tool_args)
        )
        LOGGER.info(
            f"Tool invocation completed. Tool: {tool_name}, Arguments: {tool_args}"
        )
        LOGGER.debug(f"Tool Response: {tool_response}")

        success = "error" not in tool_response
        tool_call_content = (
            json.dumps(tool_response["structured_content"])
            if success
            else json.dumps(tool_response)
        )

        if (
            agent_config.TEST_WITH_GOLDEN
            and not tool_meta.get("skip_golden_eval", False)
        ):
            LOGGER.info(
                f"Performing golden evaluation for tool call '{tool_name}' with arguments: {tool_args}"
            )
            for _ in range(agent_config.MAX_GOLDEN_RETRIES):
                golden_evaluation = self.evaluate_with_golden_config(
                    tool_name, json.loads(tool_args)
                )
                if not golden_evaluation["safe"]:
                    LOGGER.warning(
                        f"GOLDEN_EVAL: Discrepancy detected in tool call evaluation with golden config: {golden_evaluation['reason']}"
                    )
                    LOGGER.debug(
                        f"Golden Evaluation Details: {json.dumps(golden_evaluation, indent=2)}"
                    )
                else:
                    LOGGER.info(
                        f"GOLDEN_EVAL: Tool call '{tool_name}' passed golden evaluation."
                    )
                if (
                    golden_evaluation["flag"] == "no_tool_call"
                    or golden_evaluation["flag"] == "different_tool_called"
                    or golden_evaluation["flag"] == "wrong_tool_arguments"
                ):
                    LOGGER.info(
                        "Retrying golden evaluation due to no tool call or different tool called."
                    )
                else:
                    break
            self.golden_eval_hist.append(
                {
                    "tool_name": tool_name,
                    "tool_args": json.loads(tool_args),
                    "eval_result": golden_evaluation,
                }
            )

        if not success:
            self.count_tool_call_fails += 1
        if (
            safeguard_config.TOOL_END_CONVERSATION_FLAG
            and success
            and tool_meta.get("end_conversation", False)
        ):
            self.end_conversation = True
            LOGGER.info("Tool call indicates the conversation should end.")

        if (
            safeguard_config.TOOL_RESPONSE_TEMPLATE
            and success
            and tool_meta.get("response_template", None)
        ):
            if self.override_assistant_msg is None:
                self.override_assistant_msg = tool_meta["response_template"]

        if confirmation_msg:
            tool_call_content = (
                f"Tool call confirmed by user: {confirmation_msg}\n\n"
                f"Tool Response: {tool_call_content}"
            )
        self.history.append(
            {
                "role": "tool",
                "content": tool_call_content,
                "tool_call_id": tool_call.id,
            }
        )

    def ReAct_loop(self, user_input: str) -> str:
        if self.remaining_tool_call:
            self.tmp_user_response = self.tmp_user_response + "\n" + user_input
            if user_input.strip().upper().find("CONFIRM") == 0:
                LOGGER.info("User confirmed the tool invocation.")
                self._process_tool_call(
                    self.remaining_tool_call,
                    user_confirmed=True,
                    confirmation_msg=self.tmp_user_response,
                )
                self.remaining_tool_call = None
            elif user_input.strip().upper().find("CANCEL") == 0:
                LOGGER.info("User canceled the tool invocation.")
                self.history.append(
                    {
                        "role": "tool",
                        "content": f"Tool invocation canceled by user response: {self.tmp_user_response}",
                        "tool_call_id": self.remaining_tool_call.id,
                    }
                )
                self.remaining_tool_call = None
            else:
                msg = 'Please respond first with "CONFIRM" to proceed or "CANCEL" to abort. Then provide your additional notes after that if any.'
                return msg
            self.tmp_user_response = ""
        else:
            self.append_user_message(user_input)
            self.count_tool_call_fails = 0

        while True and self.count_tool_call_fails < agent_config.MAX_TOOL_CALL_FAILS:
            if self.override_assistant_msg is not None:
                self.history.append(
                    {
                        "role": "assistant",
                        "content": self.override_assistant_msg,
                    }
                )
                self.override_assistant_msg = None
                return self.history[-1]["content"]

            response = self._call_LLM(self.history, self.tools)
            self.history.append(response.to_dict())

            if response.tool_calls:
                res = self._process_tool_call(
                    response.tool_calls[0], user_confirmed=False
                )
                if res is not None:
                    self.remaining_tool_call = response.tool_calls[0]
                    return res
            else:
                return response.content
        response = self._call_LLM(self.history, [])
        self.history.append(response.to_dict())
        return response.content

    def evaluate_with_golden_config(self, tool_name: str, tool_args: Dict) -> Dict:
        golden_mcp_client = MCPClient(
            agent_config.MCP_SERVER_COMMAND, agent_config.MCP_SERVER_COMMAND_GOLDEN_ARGS
        )
        golden_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(golden_loop)
        golden_loop.run_until_complete(golden_mcp_client.initialize())
        all_tools = golden_mcp_client.list_OPENAI_tools()
        temp_hist = self.history[:-1] + [
            {
                "role": "assistant",
                "content": f"I plan to call the tool {tool_name} with arguments {json.dumps(tool_args)}. For all the additional parameters needed not included here, I will include them as well, or ask the user if I'm not sure.",
            }
        ]
        response = self._call_LLM(temp_hist, all_tools, temperature=0.6)

        def _shutdown_golden_loop():
            try:
                pending = asyncio.all_tasks(loop=golden_loop)
                for task in pending:
                    task.cancel()
                golden_loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )
                golden_loop.run_until_complete(golden_loop.shutdown_asyncgens())
            finally:
                golden_loop.close()

        if not response.tool_calls:
            _shutdown_golden_loop()
            return {
                "safe": False,
                "flag": "no_tool_call",
                "reason": "LLM did not suggest any tool calls under golden config.",
                "text_response": response.content,
            }

        tool_call = response.tool_calls[0]

        # tool call does not match
        if tool_call.function.name != tool_name:
            _shutdown_golden_loop()
            return {
                "safe": False,
                "flag": "different_tool_called",
                "reason": f"LLM suggested tool '{tool_call.function.name}' instead of expected '{tool_name}' under golden config.",
                "tool_call": tool_call.function.to_dict(),
            }
        tool_call_arguments = json.loads(tool_call.function.arguments)
        for arg_key, arg_value in tool_args.items():
            if tool_call_arguments.get(arg_key, None) != arg_value:
                _shutdown_golden_loop()
                return {
                    "safe": False,
                    "flag": "wrong_tool_arguments",
                    "reason": f"LLM suggested different argument value for '{arg_key}' under golden config.",
                    "tool_call": tool_call.function.to_dict(),
                }

        tool_response = golden_loop.run_until_complete(
            golden_mcp_client.call_tool(tool_name, tool_call.function.arguments)
        )
        golden_error_statistic = golden_loop.run_until_complete(
            golden_mcp_client.report_error_statistics()
        )
        LOGGER.debug(f"GOLDEN_EVAL: Tool Response under golden config: {tool_response}")
        LOGGER.debug(
            f"GOLDEN_EVAL: Error statistics under golden config: {golden_error_statistic}"
        )
        _shutdown_golden_loop()
        if "error" in tool_response:
            return {
                "safe": False,
                "flag": "tool_call_raised_error",
                "reason": "Tool call resulted in error under golden config.",
                "tool_response": tool_response,
                "error_statistics": golden_error_statistic,
            }
        if golden_error_statistic["raise_count_with_type"] != {}:
            return {
                "safe": False,
                "flag": "tool_call_raised_error",
                "reason": "Tool call resulted in error under golden config.",
                "tool_response": tool_response["structured_content"],
                "error_statistics": golden_error_statistic,
            }

        return {
            "safe": True,
            "flag": "pass",
            "tool_response": tool_response["structured_content"],
        }

    def _call_LLM(self, messages: list, tools: List, **kwargs) -> ChatCompletionMessage:
        client = OpenAI()
        if "temperature" not in kwargs:
            kwargs["temperature"] = self.temperature
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            parallel_tool_calls=False,
            **kwargs,
        )
        return response.choices[0].message

    def fetch_successful_tool_call_history(self) -> List[Dict]:
        return self.mcp_client.successful_tool_calls

    def get_user_and_assistant_history(self) -> List[Dict[str, str]]:
        return [msg for msg in self.history if msg["role"] in ["user", "assistant"]]

    def report_tool_error_statistics(self) -> Dict:
        return self.loop.run_until_complete(self.mcp_client.report_error_statistics())

    def shutdown(self):
        LOGGER.info("Shutting down ReActAgent and closing event loop.")
        try:
            pending = asyncio.all_tasks(loop=self.loop)
            for task in pending:
                task.cancel()
            self.loop.run_until_complete(
                asyncio.gather(*pending, return_exceptions=True)
            )
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        finally:
            self.loop.close()
        LOGGER.info("ReActAgent shutdown complete.")
