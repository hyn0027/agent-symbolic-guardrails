from openai import OpenAI
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from typing import List

from config.loader import CONFIG
from config.logger import LOGGER

user_config = CONFIG.USER


class UserSimulator:
    def __init__(self, instructions: str):
        self.model = user_config.MODEL
        self.temperature = user_config.TEMPERATURE
        self.instructions = instructions
        self.client = OpenAI()
        self.initialize()

    def get_system_prompt(self) -> str:
        with open(user_config.SIMULATION_GUIDELINE_PATH, "r") as file:
            guidelines = file.read()

        system_prompt = user_config.SYSTEM_PROMPT_TEMPLATE.format(
            global_user_sim_guidelines=guidelines, instructions=self.instructions
        )
        return system_prompt

    def initialize(self):
        self.history = [
            {
                "role": "system",
                "content": self.get_system_prompt(),
            }
        ]
        LOGGER.info("UserAgent initialization complete.")

    def respond_to_customer_support(self, customer_support_message: str) -> str:
        self.history.append({"role": "user", "content": customer_support_message})

        response = self._call_LLM(self.history, tools=[])
        self.history.append(response.to_dict())
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
