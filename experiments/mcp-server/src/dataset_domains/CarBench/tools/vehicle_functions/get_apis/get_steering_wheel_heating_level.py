import json
from typing import Any, Dict, Union

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.tool import Tool


class GetSteeringWheelHeatingLevel(Tool):
    "Vehicle Information: Get the level of the steering wheel heating."

    @staticmethod
    def invoke() -> str:
        """
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Contains the level of the steering wheel heating.
        """
        vehicle_ctx = context_state.get()
        response = {}

        steering_wheel_heating_level = vehicle_ctx.steering_wheel_heating
        response["status"] = "SUCCESS"
        response["result"] = {"steering_wheel_heating": steering_wheel_heating_level}

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "get_steering_wheel_heating_level",
                "description": "Vehicle Information: Get the level of the steering wheel heating.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
        }

    @staticmethod
    def get_output_info() -> Dict[str, Any]:
        """
        Output variable description
        """
        return {
            "type": "object",
            "properties": {
                "steering_wheel_heating": {
                    "type": "integer",
                    "description": "The current level of the steering wheel heating.",
                    "examples": [2],
                }
            },
            "required": ["steering_wheel_heating"],
            "additionalProperties": False,
        }
