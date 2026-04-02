import json
from typing import Any, Dict, Union

from pydantic import BaseModel, Field

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class SetSteeringWheelHeating(Tool):
    "Vehicle Climate Control: Sets the steering wheel heating to the specified level inside the car."

    @staticmethod
    def invoke(level: int) -> str:
        """
        Args:
            level (int): The level to set the steering wheel heating to, ranging from 0 to 3.
        Returns:
            status (str): Indicates if the tool call was an "SUCCESS" or "FAILURE".
            level (int): The level to which the steering wheel heating was set.
        """
        vehicle_ctx = context_state.get()
        response = {}

        # Check for Errors
        if level < 0 or level > 3:
            response["status"] = "FAILURE"
            error_message = "SetSteeringWheelHeating_001: Invalid level requested - only values between 0 and 3 are allowed."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SET_STEERING_WHEEL_HEATING_001": error_message}
            return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {"level": level}
        vehicle_ctx.update_state(steering_wheel_heating=level)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """
        return {
            "type": "function",
            "function": {
                "name": "set_steering_wheel_heating",
                "description": "Vehicle Climate Control: Sets the steering wheel heating to the specified level inside the car.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["level"],
                    "properties": {
                        "level": {
                            "type": "number",
                            "description": "The level to set the steering wheel heating to.",
                            "multipleOf": 1,
                            "minimum": 0,
                            "maximum": 3,
                        }
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
                "level": {
                    "type": "integer",
                    "description": "The steering wheel heating level that was set, ranging from 0 (off) to 3 (maximum).",
                    "examples": [1],
                }
            },
            "required": ["level"],
            "additionalProperties": False,
        }
