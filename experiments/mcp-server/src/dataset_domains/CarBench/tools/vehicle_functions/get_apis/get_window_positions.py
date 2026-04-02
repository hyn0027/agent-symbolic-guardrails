import json
from typing import Any, Dict, Union

from pydantic import BaseModel, Field

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.tool import Tool


class GetWindowPositions(Tool):
    "Vehicle Information: Get the current position of the windows in the car."

    @staticmethod
    def invoke() -> str:
        """
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Contains the current position of the windows in the car.
        """
        vehicle_ctx = context_state.get()
        response = {}

        description = "0 = closed, 100=open."
        window_driver_position = vehicle_ctx.window_driver_position
        window_passenger_position = vehicle_ctx.window_passenger_position
        window_driver_rear_position = vehicle_ctx.window_driver_rear_position
        window_passenger_rear_position = vehicle_ctx.window_passenger_rear_position

        response["status"] = "SUCCESS"
        response["result"] = {
            "description": description,
            "window_driver_position": window_driver_position,
            "window_passenger_position": window_passenger_position,
            "window_driver_rear_position": window_driver_rear_position,
            "window_passenger_rear_position": window_passenger_rear_position,
        }

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "get_vehicle_window_positions",
                "description": "Vehicle Information: Get the current position of the windows in the car.",
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
                "description": {
                    "type": "string",
                    "description": "Description of window position values, e.g., '0 = closed, 100 = open'.",
                    "examples": ["0 = closed, 100=open."],
                },
                "window_driver_position": {
                    "type": "integer",
                    "description": "The open percentage of the driver's window.",
                    "examples": [0],
                },
                "window_passenger_position": {
                    "type": "integer",
                    "description": "The open percentage of the passenger's window.",
                    "examples": [0],
                },
                "window_driver_rear_position": {
                    "type": "integer",
                    "description": "The open percentage of the driver rear window.",
                    "examples": [0],
                },
                "window_passenger_rear_position": {
                    "type": "integer",
                    "description": "The open percentage of the passenger rear window.",
                    "examples": [0],
                },
            },
            "required": [
                "description",
                "window_driver_position",
                "window_passenger_position",
                "window_driver_rear_position",
                "window_passenger_rear_position",
            ],
            "additionalProperties": False,
        }
