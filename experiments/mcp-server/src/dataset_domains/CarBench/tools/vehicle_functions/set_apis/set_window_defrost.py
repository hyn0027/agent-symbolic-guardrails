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


class SetWindowDefrost(Tool):
    "Vehicle Climate Control: Turns on or off the defrost of the specified window inside the car."

    @staticmethod
    def invoke(on: bool, defrost_window: str) -> str:
        """
        Args:
            on (bool): True to turn on the defrost, False to turn off the defrost.
            defrost_window (str): The window to turn on or off the defrost, can be "ALL", "FRONT", or "REAR".
        Returns:
            status (str): Indicates if the tool call was an "SUCCESS" or "FAILURE".
            defrost_window (str): The window for which the defrost was activated or deactivated.
        """
        vehicle_ctx = context_state.get()
        response = {}
        valid_defrost_window = ["ALL", "FRONT", "REAR"]
        # Check for Errors
        if defrost_window not in valid_defrost_window:
            response["status"] = "FAILURE"
            error_message = "SetWindowDefrost_001: Invalid defrost window requested - choose one of ALL, FRONT, REAR."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SET_WINDOW_DEFROST_001": error_message}
            return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {"on": on, "defrost_window": defrost_window}
        if defrost_window == "ALL":
            vehicle_ctx.update_state(window_front_defrost=on, window_rear_defrost=on)
        elif defrost_window == "FRONT":
            vehicle_ctx.update_state(window_front_defrost=on)
        elif defrost_window == "REAR":
            vehicle_ctx.update_state(window_rear_defrost=on)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """
        return {
            "type": "function",
            "function": {
                "name": "set_window_defrost",
                "description": "Vehicle Climate Control: Turns on or off the defrost of the specified window inside the car.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["on", "defrost_window"],
                    "properties": {
                        "on": {
                            "type": "boolean",
                            "description": "True to turn on the defrost, False to turn off the defrost.",
                        },
                        "defrost_window": {
                            "type": "string",
                            "description": "The window to turn on or off the defrost.",
                            "enum": ["ALL", "FRONT", "REAR"],
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
                "on": {
                    "type": "boolean",
                    "description": "Indicates whether the window defrost was turned on (true) or off (false).",
                    "examples": [True],
                },
                "defrost_window": {
                    "type": "string",
                    "description": "The window for which the defrost was activated; this is one of 'ALL', 'FRONT', or 'REAR'.",
                    "examples": ["FRONT"],
                },
            },
            "required": ["on", "defrost_window"],
            "additionalProperties": False,
        }
