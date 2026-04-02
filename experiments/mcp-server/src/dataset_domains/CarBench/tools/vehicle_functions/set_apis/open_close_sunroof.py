import json
from typing import Any, Dict, Literal, TypeAlias, Union

from pydantic import BaseModel, Field

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class OpenCloseSunroof(Tool):
    "Vehicle Control: Open or close the sunroof in the car to a specified percentage: 0 (closed) to 100 (open)"

    @staticmethod
    def invoke(percentage: int) -> str:
        """
        Args:
            percentage (int): The percentage to open the sunroof, ranging from 0 to 100.
        Returns:
            status (str): Indicates if the tool call was an "SUCCESS" or "FAILURE".
            percentage (int): The percentage to which the sunroof was opened.
        """
        vehicle_ctx = context_state.get()
        response = {}

        # --- Error Handling ---
        if percentage < 0 or percentage > 100:
            response["status"] = "FAILURE"
            error_message = "OpenCloseSunroof_001: Invalid percentage requested - only values between 0-100 are allowed."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"OPEN_CLOSE_SUNROOF_001": error_message}
            return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {"percentage": percentage}
        vehicle_ctx.update_state(sunroof_position=percentage)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "open_close_sunroof",
                "description": "Vehicle Control: Open or close the sunroof in the car to a specified percentage: 0 (closed) to 100 (open)",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["percentage"],
                    "properties": {
                        "percentage": {
                            "type": "number",
                            "description": "The percentage to open the sunroof, ranging from 0 to 100",
                            "multipleOf": 1,
                            "minimum": 0,
                            "maximum": 100,
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
                "percentage": {
                    "type": "integer",
                    "description": "The percentage to which the sunroof was set.",
                    "examples": [75],
                }
            },
            "required": ["percentage"],
            "additionalProperties": False,
        }
