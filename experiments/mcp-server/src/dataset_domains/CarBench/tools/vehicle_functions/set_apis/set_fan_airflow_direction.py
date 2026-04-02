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


class SetFanAirflowDirection(Tool):
    "Vehicle Climate Control: Set fan airflow direction inside the car."

    @staticmethod
    def invoke(direction: str) -> str:
        """
        Args:
            direction (str): The airflow direction to set the fans to, can be "FEET", "HEAD", "HEAD_FEET", "WINDSHIELD", "WINDSHIELD_FEET", "WINDSHIELD_HEAD", or "WINDSHIELD_HEAD_FEET".
        Returns:
            status (str): Indicates if the tool call was an "SUCCESS" or "FAILURE".
            direction (str): The airflow direction that was set.
        """
        vehicle_ctx = context_state.get()
        response = {}
        valid_direction = [
            "FEET",
            "HEAD",
            "HEAD_FEET",
            "WINDSHIELD",
            "WINDSHIELD_FEET",
            "WINDSHIELD_HEAD",
            "WINDSHIELD_HEAD_FEET",
        ]
        # Check for Errors
        if direction not in valid_direction:
            response["status"] = "FAILURE"
            error_message = "SetFanAirflowDirection_001: Invalid defrost window requested - choose one of FEET, HEAD, HEAD_FEET, WINDSHIELD, WINDSHIELD_FEET, WINDSHIELD_HEAD, WINDSHIELD_HEAD_FEET."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SET_FAN_AIRFLOW_DIRECTION_001": error_message}
            return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {"direction": direction}
        vehicle_ctx.update_state(fan_airflow_direction=direction)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """
        return {
            "type": "function",
            "function": {
                "name": "set_fan_airflow_direction",
                "description": "Vehicle Climate Control: Set fan airflow direction inside the car.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["direction"],
                    "properties": {
                        "direction": {
                            "type": "string",
                            "description": "The airflow direction to set the fans to.",
                            "enum": [
                                "FEET",
                                "HEAD",
                                "HEAD_FEET",
                                "WINDSHIELD",
                                "WINDSHIELD_FEET",
                                "WINDSHIELD_HEAD",
                                "WINDSHIELD_HEAD_FEET",
                            ],
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
                "direction": {
                    "type": "string",
                    "description": "The fan airflow direction that was set.",
                    "examples": ["WINDSHIELD"],
                }
            },
            "required": ["direction"],
            "additionalProperties": False,
        }
