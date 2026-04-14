import json
from typing import Any, Dict, Literal, TypeAlias, Union

from pydantic import BaseModel, Field

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.tool import Tool

from config_loader import CONFIG

safeguard_config = CONFIG.SAFEGUARD


class SetHeadLightsHighBeams(Tool):
    "Vehicle Control: Turns the high beam headlights outside the car on or off."

    @staticmethod
    def invoke(on: bool) -> str:
        """
        Args:
            on (bool): True to turn on the high beam headlights, False to turn off the high beam headlights.
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
        """
        vehicle_ctx = context_state.get()
        response = {}
        if safeguard_config.API_CHECK: # AUT-POL:014
            if on:
                previous_tool_calls = set(
                    [tool_call["name"] for tool_call in Tool.all_tool_calls]
                )
                if vehicle_ctx.fog_lights:
                    response["status"] = "REJECTED_BY_GUARDRAIL"
                    error_message = "Violating policy AUT-POL:014: The high beam headlights cannot be turned ON if the fog lights are currently ON. Please first turn off the fog lights before turning on the high beam headlights."
                    response["errors"] = {"AUT-POL:014": error_message}
                    return json.dumps(response)
                if not (
                    "get_exterior_lights_status" in previous_tool_calls
                    or "set_fog_lights" in previous_tool_calls
                ):
                    response["status"] = "REJECTED_BY_GUARDRAIL"
                    error_message = "Violating policy AUT-POL:014: The high beam headlights cannot be turned ON if the fog lights are currently ON. Please first check the status of the fog lights before turning on the high beam headlights. If the fog lights are currently ON, please turn them OFF before turning on the high beam headlights."
                    response["errors"] = {"AUT-POL:014": error_message}
                    return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {"on": on}
        vehicle_ctx.update_state(head_lights_high_beams=on)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "set_head_lights_high_beams",
                "description": "REQUIRES_CONFIRMATION, Vehicle Control: Turns the high beam headlights outside the car on or off.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["on"],
                    "properties": {
                        "on": {
                            "type": "boolean",
                            "description": "True to turn on the high beam headlights, False to turn off the high beam headlights.",
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
                "on": {
                    "type": "boolean",
                    "description": "Indicates whether the high beam headlights were turned on (true) or off (false).",
                    "examples": [True],
                }
            },
            "required": ["on"],
            "additionalProperties": False,
        }
