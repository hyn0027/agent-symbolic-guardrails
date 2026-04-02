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


class SetAirCirculation(Tool):
    "Vehicle Climate Control: Set the mode of air circulation to draw fresh air or recirculate air inside the car."

    # TODO: write set_air_circulation
    @staticmethod
    def invoke(mode: str) -> str:
        """
        Args:
            mode (str): The mode in which the air should be circulated, can be "FRESH_AIR", "RECIRCULATION", or "AUTO".
        Returns:
            status (str): Indicates if the tool call was an "SUCCESS" or "FAILURE".
            mode (str): The mode to which the air circulation was set.
        """
        vehicle_ctx = context_state.get()
        response = {}

        valid_mode = ["FRESH_AIR", "RECIRCULATION", "AUTO"]
        # --- Error Handling ---
        if mode not in valid_mode:
            response["status"] = "FAILURE"
            error_message = "SetAirCirculation_001: Invalid air circulation mode requested - choose one of FRESH_AIR, RECIRCULATION, AUTO."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SET_AIR_CIRCULATION_001": error_message}
            return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {"mode": mode}
        vehicle_ctx.update_state(air_circulation=mode)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """
        return {
            "type": "function",
            "function": {
                "name": "set_air_circulation",
                "description": "Vehicle Climate Control: Set the mode of air circulation to draw fresh air or recirculate air inside the car.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["mode"],
                    "properties": {
                        "mode": {
                            "type": "string",
                            "description": "In which mode the air should be circulated.",
                            "enum": ["FRESH_AIR", "RECIRCULATION", "AUTO"],
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
                "mode": {
                    "type": "string",
                    "description": "The air circulation mode that was set.",
                    "examples": ["AUTO"],
                }
            },
            "required": ["mode"],
            "additionalProperties": False,
        }
