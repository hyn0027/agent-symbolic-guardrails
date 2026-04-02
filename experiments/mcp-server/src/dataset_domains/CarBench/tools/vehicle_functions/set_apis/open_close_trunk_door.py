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


class OpenCloseTrunkDoor(Tool):
    "Vehicle Control: Open or close the trunk door of the car"

    @staticmethod
    def invoke(action: str) -> str:
        """
        Args:
            action (str): Whether to open or close the trunk door.
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
        """
        vehicle_ctx = context_state.get()
        response = {}

        # --- Error Handling ---
        valid_trunk_door_actions = ["OPEN", "CLOSE"]
        if action not in valid_trunk_door_actions:
            response["status"] = "FAILURE"
            error_message = "OpenCloseTrunkDoor_001: Invalid action requested - only 'OPEN' and 'CLOSE' are allowed."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"OPEN_CLOSE_TRUNK_DOOR_001": error_message}
            return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {"action": action}
        vehicle_ctx.update_state(trunk_door_position=action)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "open_close_trunk_door",
                "description": "REQUIRES_CONFIRMATION, Vehicle Control: Open or close the trunk door of the car",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["action"],
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "Whether to open or close the trunk door.",
                            "enum": ["OPEN", "CLOSE"],
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
                "action": {
                    "type": "string",
                    "description": "The trunk door action that was performed.",
                    "examples": ["OPEN"],
                }
            },
            "required": ["action"],
            "additionalProperties": False,
        }
