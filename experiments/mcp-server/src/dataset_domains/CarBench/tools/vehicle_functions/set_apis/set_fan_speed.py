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


class SetFanSpeed(Tool):
    "Vehicle Climate Control: Sets the fan speed to the specified level inside the car."

    @staticmethod
    def invoke(level: int) -> str:
        """
        Args:
            level (int): The level to set the fan speed to, ranging from 0 to 5.
        Returns:
            status (str): Indicates if the tool call was an "SUCCESS" or "FAILURE".
            level (int): The level to which the fan speed was set.
        """
        vehicle_ctx = context_state.get()
        response = {}

        # Check for Errors
        if level < 0 or level > 5:
            response["status"] = "FAILURE"
            error_message = "SetFanSpeed_001: Invalid level requested - only values between 0 and 5 are allowed."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SET_FAN_SPEED_001": error_message}
            return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {"level": level}
        vehicle_ctx.update_state(fan_speed=level)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """
        return {
            "type": "function",
            "function": {
                "name": "set_fan_speed",
                "description": "Vehicle Climate Control: Sets the fan speed to the specified level inside the car.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["level"],
                    "properties": {
                        "level": {
                            "type": "number",
                            "description": "The level to set the fan speed to.",
                            "multipleOf": 1,
                            "minimum": 0,
                            "maximum": 5,
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
                    "description": "The fan speed level that was set, ranging from 0 (off) to 5 (maximum).",
                    "examples": [3],
                }
            },
            "required": ["level"],
            "additionalProperties": False,
        }
