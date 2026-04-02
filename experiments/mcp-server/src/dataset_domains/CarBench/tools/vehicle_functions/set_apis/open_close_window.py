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


class OpenCloseWindow(Tool):
    "Vehicle Control: Moves the specified window in the car to a certain percentage open or closed."

    @staticmethod
    def invoke(window: str, percentage: int) -> str:
        """
        Args:
            window (str): Which window to move. Use 'ALL' to refer to all windows.
            percentage (int): Percentage to open or close the specified window or windows, ranging from 0 to 100.
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
        """
        vehicle_ctx = context_state.get()
        response = {}

        valid_windows = [
            "ALL",
            "DRIVER",
            "PASSENGER",
            "DRIVER_REAR",
            "PASSENGER_REAR",
            "RIGHT_REAR",
            "LEFT_REAR",
        ]
        # --- Error Handling ---
        if percentage < 0 or percentage > 100:
            response["status"] = "FAILURE"
            error_message = "OpenCloseWindow_001: Invalid percentage requested - only values between 0-100 are allowed."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"OPEN_CLOSE_WINDOW_001": error_message}
            return json.dumps(response)
        elif type(window) == list:
            response["status"] = "FAILURE"
            error_message = "OpenCloseWindow_002: Only one window or all can be controlled - for multiple specific instances, multiple parallel tool calls are needed."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"OPEN_CLOSE_WINDOW_002": error_message}
            return json.dumps(response)
        elif window not in valid_windows:
            response["status"] = "FAILURE"
            error_message = "OpenCloseWindow_003: Invalid window requested - Choose one of ALL, DRIVER, PASSENGER, DRIVER_REAR, PASSENGER_REAR, RIGHT_REAR, LEFT_REAR."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"OPEN_CLOSE_WINDOW_003": error_message}
            return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {"window": window, "percentage": percentage}
        if window == "ALL":
            vehicle_ctx.update_state(
                window_driver_position=percentage,
                window_passenger_position=percentage,
                window_driver_rear_position=percentage,
                window_passenger_rear_position=percentage,
            )
        elif window == "DRIVER":
            vehicle_ctx.update_state(window_driver_position=percentage)
        elif window == "PASSENGER":
            vehicle_ctx.update_state(window_passenger_position=percentage)
        elif window == "DRIVER_REAR" or window == "RIGHT_REAR":
            vehicle_ctx.update_state(window_driver_rear_position=percentage)
        elif window == "PASSENGER_REAR" or window == "LEFT_REAR":
            vehicle_ctx.update_state(window_passenger_rear_position=percentage)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "open_close_window",
                "description": "Vehicle Control: Moves the specified window in the car to a certain percentage open or closed.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["window", "percentage"],
                    "properties": {
                        "window": {
                            "type": "string",
                            "description": "Which window to move. Use 'ALL' to refer to all windows.",
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
                        "percentage": {
                            "type": "number",
                            "description": "Percentage to open or close the specified window or windows, ranging from 0 to 100.",
                            "multipleOf": 1,
                            "minimum": 0,
                            "maximum": 100,
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
                "window": {
                    "type": "string",
                    "description": "The identifier for the window that was moved.",
                    "examples": ["DRIVER"],
                },
                "percentage": {
                    "type": "integer",
                    "description": "The percentage to which the specified window was set.",
                    "examples": [80],
                },
            },
            "required": ["window", "percentage"],
            "additionalProperties": False,
        }
