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
        self.mcp_client = MCPClient(agent_config.MCP_SERVER_COMMAND)
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

        self.remaining_tool_calls = []
        self.tmp_user_response = ""

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

        if safeguard_config.USER_CONFIRMATION and not user_confirmed:
            tool_meta = self.mcp_client.get_tool_metadata(tool_name)
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

        tool_response = self.loop.run_until_complete(
            self.mcp_client.call_tool(tool_name, tool_args)
        )
        LOGGER.info(
            f"Tool invocation completed. Tool: {tool_name}, Arguments: {tool_args}"
        )
        LOGGER.debug(f"Tool Response: {tool_response}")
        tool_call_content = (
            json.dumps(tool_response["structured_content"])
            if "error" not in tool_response
            else json.dumps(tool_response)
        )
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

    def ReAct_loop(self, user_input: str) -> Dict:
        if self.remaining_tool_calls:
            self.tmp_user_response = self.tmp_user_response + "\n" + user_input
            if user_input.strip().upper().find("CONFIRM") == 0:
                LOGGER.info("User confirmed the tool invocation.")
                self._process_tool_call(
                    self.remaining_tool_calls[0],
                    user_confirmed=True,
                    confirmation_msg=self.tmp_user_response,
                )
                self.remaining_tool_calls = self.remaining_tool_calls[1:]
            elif user_input.strip().upper().find("CANCEL") == 0:
                LOGGER.info("User canceled the tool invocation.")
                self.history.append(
                    {
                        "role": "tool",
                        "content": f"Tool invocation canceled by user response: {self.tmp_user_response}",
                        "tool_call_id": self.remaining_tool_calls[0].id,
                    }
                )
                self.remaining_tool_calls = self.remaining_tool_calls[1:]
            else:
                msg = 'Please respond with "CONFIRM" to proceed or "CANCEL" to abort.'
                return msg
            self.tmp_user_response = ""
            for index, tool_call in enumerate(self.remaining_tool_calls):
                res = self._process_tool_call(tool_call, user_confirmed=False)
                if res is not None:
                    self.remaining_tool_calls = self.remaining_tool_calls[index:]
                    return res
            self.remaining_tool_calls = []
        else:
            self.append_user_message(user_input)

        while True:
            response = self._call_LLM(self.history, self.tools)
            self.history.append(response.to_dict())

            if response.tool_calls:
                for index, tool_call in enumerate(response.tool_calls):
                    res = self._process_tool_call(tool_call, user_confirmed=False)
                    if res is not None:
                        self.remaining_tool_calls = response.tool_calls[index:]
                        return res
            else:
                return response.content

    def _call_LLM(self, messages: list, tools: List) -> ChatCompletionMessage:
        client = OpenAI()
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            tools=tools,
        )
        return response.choices[0].message

    def fetch_tool_call_history(self) -> List[Dict]:
        tool_calls = []
        for message in self.history:
            if message.get("role") == "assistant" and "tool_calls" in message:
                tool_calls.extend(message["tool_calls"])
        return tool_calls

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
