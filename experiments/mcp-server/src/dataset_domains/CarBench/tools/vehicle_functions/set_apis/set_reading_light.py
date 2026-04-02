import json
from typing import Any, Dict, Literal, TypeAlias, Union

from pydantic import BaseModel, Field

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.policy_evaluator import policy_errors_during_runtime
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class SetReadingLight(Tool):
    "Vehicle Control: Turns the specified reading light in the car on or off."

    @staticmethod
    def invoke(position: str, on: bool) -> str:
        """
        Args:
            position (str): Which reading light to turn on or off. Use 'ALL' to refer to all reading lights.
            on (bool): True to turn on the reading light, False to turn off the reading light.
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
        """
        vehicle_ctx = context_state.get()
        response = {}
        valid_position = [
            "ALL",
            "DRIVER",
            "PASSENGER",
            "DRIVER_REAR",
            "PASSENGER_REAR",
            "RIGHT_REAR",
            "LEFT_REAR",
        ]
        # Check for Errors
        if type(position) == list:
            response["status"] = "FAILURE"
            error_message = "SetReadingLight_001: Only one reading light or all can be controlled - for multiple specific instances, multiple parallel tool calls are needed."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SET_READING_LIGHT_001": error_message}
            return json.dumps(response)

        elif position not in valid_position:
            response["status"] = "FAILURE"
            error_message = "SetReadingLight_002: Invalid position requested - Choose one of ALL, DRIVER, PASSENGER, DRIVER_REAR, PASSENGER_REAR, RIGHT_REAR, LEFT_REAR."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SET_READING_LIGHT_002": error_message}
            return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {"position": position}
        if position == "ALL":
            vehicle_ctx.update_state(
                reading_light_driver=on,
                reading_light_passenger=on,
                reading_light_driver_rear=on,
                reading_light_passenger_rear=on,
            )
        elif position == "DRIVER":
            vehicle_ctx.update_state(reading_light_driver=on)
        elif position == "PASSENGER":
            vehicle_ctx.update_state(reading_light_passenger=on)
        elif position == "DRIVER_REAR" or position == "RIGHT_REAR":
            vehicle_ctx.update_state(reading_light_driver_rear=on)
        elif position == "PASSENGER_REAR" or position == "LEFT_REAR":
            vehicle_ctx.update_state(reading_light_passenger_rear=on)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "set_reading_light",
                "description": "Vehicle Control: Turns the specified reading light in the car on or off.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["position", "on"],
                    "properties": {
                        "position": {
                            "type": "string",
                            "description": "Which reading light to turn on or off. Use 'ALL' to refer to all reading lights.",
                            "enum": [
                                "ALL",
                                "DRIVER",
                                "PASSENGER",
                                "DRIVER_REAR",
                                "PASSENGER_REAR",
                                "RIGHT_REAR",
                                "LEFT_REAR",
                            ],
                        },
                        "on": {
                            "type": "boolean",
                            "description": "True to turn on the reading light, False to turn off the reading light.",
                        },
                    },
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
                "position": {
                    "type": "string",
                    "description": "The reading light position that was controlled. This indicates which reading light (or all) was targeted.",
                    "examples": ["DRIVER"],
                }
            },
            "required": ["position"],
            "additionalProperties": False,
        }
