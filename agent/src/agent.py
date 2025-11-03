from openai import OpenAI
import json
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from typing import Dict, List
import asyncio
from mcp_client import MCPClient
from config import LOGGER, CONFIG

config = CONFIG.AGENT


class ReActAgent:
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.0):
        self.model = model
        self.temperature = temperature
        self.mcp_client = MCPClient(config.MCP_SERVER_COMMAND)
        self.initialize()

    def initialize(self):
        asyncio.run(self.mcp_client.initialize())
        self.tools = self.mcp_client.list_OPENAI_tools()
        self.history = [
            {"role": "system", "content": self.system_prompt},
        ]
        LOGGER.info(f"Agent initialization complete. Detected {len(self.tools)} tools.")
        LOGGER.info("Available tools have been successfully enumerated.")
        LOGGER.debug(json.dumps(self.tools, indent=2))

    @property
    def domain_policy(self) -> str:
        with open(config.DOMAIN_POLICY_FILE, "r") as f:
            domain_policy = f.read().strip()
        return domain_policy

    @property
    def system_prompt(self) -> str:
        return config.SYSTEM_PROMPT_TEMPLATE.format(
            agent_instruction=config.AGENT_INSTRUCTION,
            domain_policy=self.domain_policy,
        )

    def ReAct_loop(self, user_input: str) -> Dict:
        self.history.append({"role": "user", "content": user_input})

        while True:
            response = self._call_LLM(self.history, self.tools)
            self.history.append(response.to_dict())

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = tool_call.function.arguments

                    tool_response = asyncio.run(
                        self.mcp_client.call_tool(tool_name, tool_args)
                    )
                    LOGGER.info(
                        f"Tool invocation completed. Tool: {tool_name}, Arguments: {tool_args}"
                    )
                    LOGGER.debug(f"Tool Response: {tool_response}")
                    self.history.append(
                        {
                            "role": "tool",
                            "content": (
                                tool_response.text
                                if "error" not in tool_response
                                else json.dumps(tool_response)
                            ),
                            "tool_call_id": tool_call.id,
                        }
                    )
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
