from openai import OpenAI
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from typing import List, Dict

from config.loader import CONFIG
from config.logger import LOGGER

user_config = CONFIG.USER


class UserSimulator:
    def __init__(self, system_prompt: str):
        assert isinstance(user_config.MODEL, str), "MODEL should be a string."
        assert isinstance(
            user_config.TEMPERATURE, float
        ), "TEMPERATURE should be a float."
        self.model = user_config.MODEL
        self.temperature = user_config.TEMPERATURE
        self.system_prompt = system_prompt
        self.client = OpenAI()
        self.initialize()
        self.history: List[Dict] = []

    def initialize(self) -> None:
        self.history = [
            {
                "role": "system",
                "content": self.system_prompt,
            }
        ]
        LOGGER.info("UserAgent initialization complete.")

    def respond_to_customer_support(self, customer_support_message: str) -> str:
        self.history.append({"role": "user", "content": customer_support_message})

        response = self._call_LLM(self.history, tools=[])
        self.history.append(response.to_dict())

        assert isinstance(
            response.content, str
        ), "LLM response message content is not a string."

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
        return []
