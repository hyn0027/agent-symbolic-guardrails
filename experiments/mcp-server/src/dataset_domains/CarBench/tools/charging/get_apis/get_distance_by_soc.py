import json
from typing import Any, Dict, Optional, Union

from dataset_domains.CarBench.context.fixed_context import fixed_context
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class GetDistanceBySoc(Tool):
    "Vehicle Information: Get the distance able to drive for a specified initial state until a final state of charge of the car."

    @staticmethod
    def invoke(
        initial_state_of_charge: int,
        final_state_of_charge: Optional[int] = 0,
    ) -> str:
        """
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Contains the current charging status of the electric vehicle.
            errors (dict): Error messages if the tool call was a "FAILURE".
        """
        fixed_ctx = fixed_context.get()
        response = {}

        # --- Error Handling ---
        if initial_state_of_charge < final_state_of_charge:
            response["status"] = "FAILURE"
            error_message = "GetDistanceBySoc_001: Invalid request - initial_state_of_charge cannot be less than final_state_of_charge."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_DISTANCE_BY_SOC_001": error_message}
            return json.dumps(response)

        energy = ((initial_state_of_charge - final_state_of_charge) / 100) * (
            fixed_ctx.battery_capacity_kwh
            * (fixed_ctx.useable_battery_percentage / 100)
        )
        # assuming the fixed energy consumption already factors in current power consumption, expected power consumption if route selected, or base power consumption if standing
        range = (energy / fixed_ctx.energy_consumption) * 100

        # --- Response ---
        response["status"] = "SUCCESS"
        response["result"] = {
            f"distance_km_for_{initial_state_of_charge}_until_{final_state_of_charge}_percent_soc": f"{round(range, 0)}km"
        }

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "get_distance_by_soc",
                "description": "Charging Information: Get the distance able to drive for a specified initial state until a final state of charge of the car.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["initial_state_of_charge"],
                    "properties": {
                        "initial_state_of_charge": {
                            "type": "integer",
                            "description": "The initial state of charge of the electric vehicle.",
                            "minimum": 0,
                            "maximum": 100,
                        },
                        "final_state_of_charge": {
                            "type": "integer",
                            "description": "The final state of charge of the electric vehicle. Defaults to 0 (battery empty).",
                            "minimum": 0,
                            "maximum": 100,
                            "default": 0,
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
                "distance_km_for_initial_until_final_percent_soc": {
                    "type": "string",
                    "description": "The distance in kilometers that can be driven from the initial state of charge to the final state of charge.",
                    "examples": ["150 km"],
                }
            },
            "required": ["distance_km_for_initial_until_final_percent_soc"],
            "additionalProperties": False,
        }
