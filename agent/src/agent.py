from openai import OpenAI
import json
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from typing import Dict, List
import asyncio
from mcp_client import MCPClient
from utils import load_config, Config, get_logger

config = load_config("config.yml")

logger = get_logger("ReActAgent", config.log_dir)


class ReActAgent:
    def __init__(self, config: Config, model: str = "gpt-4o", temperature: float = 0.0):
        self.model = model
        self.temperature = temperature
        self.mcp_client = MCPClient()
        self.config = config
        self.initialize()

    def initialize(self):
        asyncio.run(self.mcp_client.initialize())
        self.tools = self.mcp_client.list_OPENAI_tools()
        self.history = [
            {"role": "system", "content": self.system_prompt},
        ]
        logger.info(f"Agent initialization complete. Detected {len(self.tools)} tools.")
        logger.info("Available tools have been successfully enumerated.")
        logger.debug(json.dumps(self.tools, indent=2))

    @property
    def domain_policy(self) -> str:
        with open(self.config.domain_policy_file, "r") as f:
            domain_policy = f.read().strip()
        return domain_policy

    @property
    def system_prompt(self) -> str:
        return self.config.system_prompt_template.format(
            agent_instruction=self.config.agent_instruction,
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
                    logger.info(
                        f"Tool invocation completed. Tool: {tool_name}, Arguments: {tool_args}"
                    )
                    logger.debug(f"Tool Response: {tool_response}")
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


def main():
    logger.debug(config)
    agent = ReActAgent(config=config)
    while True:
        user_input = input("User: ")
        logger.debug(f"User Input: {user_input}")
        if user_input.lower() in ["exit", "quit"]:
            logger.info("Exiting the agent.")
            break
        response = agent.ReAct_loop(user_input)
        logger.info(f"Agent Response: {response}")


if __name__ == "__main__":
    main()
