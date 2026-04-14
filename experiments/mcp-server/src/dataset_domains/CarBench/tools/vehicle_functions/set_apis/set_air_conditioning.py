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
from config_loader import CONFIG

safeguard_config = CONFIG.SAFEGUARD


class SetAirConditioning(Tool):
    "Vehicle Climate Control: Turns on or off the air conditioning (AC) inside the car."

    # TODO: write set_air_conditioning
    @staticmethod
    def invoke(on: bool) -> str:
        """
        Args:
            on (bool): True to turn on the air conditioning, False to turn off the air conditioning.
        Returns:
            status (str): Indicates if the tool call was an "SUCCESS" or "FAILURE".
            on (bool): The state of the air conditioning after the operation.
        """
        vehicle_ctx = context_state.get()
        response = {}
        # no errors yet for SetAirConditioning
        if safeguard_config.API_CHECK:  # AUT-POL:011
            if on:
                previous_tool_calls = set(
                    [tool_call["name"] for tool_call in Tool.all_tool_calls]
                )
                if (
                    vehicle_ctx.window_driver_position > 20
                    or vehicle_ctx.window_passenger_position > 20
                    or vehicle_ctx.window_driver_rear_position > 20
                    or vehicle_ctx.window_passenger_rear_position > 20
                ):
                    response["status"] = "REJECTED_BY_GUARDRAIL"
                    error_message = "Violating policy AUT-POL:011: When activating the air conditioning, all windows must be closed if they are open more than 20%. Please close all windows that are open more than 20%, before activating the air conditioning."
                    response["errors"] = {"AUT-POL:011": error_message}
                    tool_execution_errors_during_runtime.get().append(error_message)
                    return json.dumps(response)
                if vehicle_ctx.fan_speed == 0:
                    response["status"] = "REJECTED_BY_GUARDRAIL"
                    error_message = "Violating policy AUT-POL:011: When activating the air conditioning, if the current fan speed is at level 0, the fan speed must be set to at least level 1. Please increase the fan speed to at least level 1 before activating the air conditioning."
                    response["errors"] = {"AUT-POL:011": error_message}
                    tool_execution_errors_during_runtime.get().append(error_message)
                    return json.dumps(response)
                if not (
                    "get_climate_settings" in previous_tool_calls
                    or "set_fan_speed" in previous_tool_calls
                ) or not (
                    "get_vehicle_window_positions" in previous_tool_calls
                    or "open_close_window" in previous_tool_calls
                ):
                    response["status"] = "REJECTED_BY_GUARDRAIL"
                    error_message = "Violating policy AUT-POL:011: When setting the air conditioning to ON, the system must have information about the current climate settings (either through get_climate_settings or through set_fan_speed) and the current window positions (either through get_vehicle_window_positions or open_close_window). Please retrieve the necessary climate settings and window position information before activating the air conditioning."
                    tool_execution_errors_during_runtime.get().append(error_message)
                    return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {"on": on}
        vehicle_ctx.update_state(air_conditioning=on)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """
        return {
            "type": "function",
            "function": {
                "name": "set_air_conditioning",
                "description": "Vehicle Climate Control: Turns on or off the air conditioning (AC) inside the car.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["on"],
                    "properties": {
                        "on": {
                            "type": "boolean",
                            "description": "True to turn on the air conditioning, False to turn off the air conditioning.",
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
                    "description": "Indicates the state of the air conditioning after the operation.",
                    "examples": [True],
                }
            },
            "required": ["on"],
            "additionalProperties": False,
        }
