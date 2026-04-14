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
from config_loader import CONFIG

safeguard_config = CONFIG.SAFEGUARD


class SetFogLights(Tool):
    "Vehicle Control: Turns the fog lights outside the car on or off."

    # TODO: write set_fog_lights
    @staticmethod
    def invoke(on: bool) -> str:
        """
        Args:
            on (bool): True to turn on the fog lights, False to turn off the fog lights.
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
        """
        vehicle_ctx = context_state.get()
        response = {}

        if safeguard_config.API_CHECK:  # AUT-POL:008
            if on:
                all_previous_tool_calls_names = set(
                    [tool_call["name"] for tool_call in Tool.all_tool_calls]
                )
                if "get_weather" not in all_previous_tool_calls_names:
                    response["status"] = "REJECTED_BY_GUARDRAIL"
                    error_message = "Violating policy AUT-POL:008: The fog lights can only be turned on if the current weather condition is known (i.e., the get_weather tool has been called at least once before). Otherwise the operation will be blocked."
                    response["errors"] = {"AUT-POL:009": error_message}
                    tool_execution_errors_during_runtime.get().append(error_message)
                    return json.dumps(response)
        if safeguard_config.API_CHECK:  # AUT-POL:013
            if on:
                previous_tool_calls = set(
                    [tool_call["name"] for tool_call in Tool.all_tool_calls]
                )
                if vehicle_ctx.head_lights_low_beams == False:
                    response["status"] = "REJECTED_BY_GUARDRAIL"
                    error_message = "Violating policy AUT-POL:013: When activating the fog lights, if the low beam headlights are currently OFF, they must be turned ON. Please turn on the low beam headlights before activating the fog lights."
                    response["errors"] = {"AUT-POL:013": error_message}
                    tool_execution_errors_during_runtime.get().append(error_message)
                    return json.dumps(response)
                if vehicle_ctx.head_lights_high_beams == True:
                    response["status"] = "REJECTED_BY_GUARDRAIL"
                    error_message = "Violating policy AUT-POL:013: When activating the fog lights, if the high beam headlights are currently ON, they must be turned OFF. Please turn off the high beam headlights before activating the fog lights."
                    response["errors"] = {"AUT-POL:013": error_message}
                    tool_execution_errors_during_runtime.get().append(error_message)
                    return json.dumps(response)
                if not (
                    "get_exterior_lights_status" in previous_tool_calls
                    or (
                        "set_head_lights_low_beams" in previous_tool_calls
                        and "set_head_lights_high_beams" in previous_tool_calls
                    )
                ):
                    response["status"] = "REJECTED_BY_GUARDRAIL"
                    error_message = "Violating policy AUT-POL:013: When activating the fog lights, the system must check if low beam headlights are ON, and if not, activate them, and check if high beam headlights are OFF, and if not, deactivate them. Please ensure that the get_exterior_lights_status tool has been called at least once before, or that the set_head_lights_low_beams and set_head_lights_high_beams tools have been called at least once before activating the fog lights."
                    response["errors"] = {"AUT-POL:013": error_message}
                    tool_execution_errors_during_runtime.get().append(error_message)
                    return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {"on": on}  #
        vehicle_ctx.update_state(fog_lights=on)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "set_fog_lights",
                "description": "Vehicle Control: Turns the fog lights outside the car on or off.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["on"],
                    "properties": {
                        "on": {
                            "type": "boolean",
                            "description": "True to turn on the fog lights, False to turn off the fog lights.",
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
                    "description": "Indicates whether the fog lights were turned on (true) or off (false).",
                    "examples": [True],
                }
            },
            "required": ["on"],
            "additionalProperties": False,
        }
