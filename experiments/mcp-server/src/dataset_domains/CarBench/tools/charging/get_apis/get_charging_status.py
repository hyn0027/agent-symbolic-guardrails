import json
from typing import Any, Dict, Union

from dataset_domains.CarBench.context.fixed_context import fixed_context
from dataset_domains.CarBench.tools.tool import Tool


class GetChargingStatus(Tool):
    "Vehicle Information: Get the current charging status of the electric vehicle. This includes state_of_charge and remaining_range based on current power consumption or base power consumption if standing."

    @staticmethod
    def invoke() -> str:
        """
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Contains the current charging status of the electric vehicle.
            errors (dict): Error messages if the tool call was a "FAILURE".
        """
        fixed_ctx = fixed_context.get()
        response = {}

        # --- Tool Execution ---
        current_soc = fixed_ctx.state_of_charge
        remaining_energy = (current_soc / 100) * (
            fixed_ctx.battery_capacity_kwh
            * (fixed_ctx.useable_battery_percentage / 100)
        )
        # assuming the fixed energy consumption already factors in current power consumption, expected power consumption if route selected, or base power consumption if standing
        remaining_range = (remaining_energy / fixed_ctx.energy_consumption) * 100

        # --- Response ---
        response["status"] = "SUCCESS"
        response["result"] = {
            "battery_capacity_kwh": fixed_ctx.battery_capacity_kwh,
            "max_charging_power_ac": fixed_ctx.max_charging_power_ac,
            "max_charging_power_dc": fixed_ctx.max_charging_power_dc,
            "state_of_charge": current_soc,
            "remaining_range": f"{round(remaining_range, 0)}km",
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
                "name": "get_charging_specs_and_status",
                "description": "Charging Information: Get the charging specs of the car and current charging status of the electric vehicle. This includes battery_capacity_kwh, max_charging_power_ac, max_charging_power_dc, state_of_charge and remaining_range (calculated based on current power consumption, expected power consumption if route selected, or base power consumption if standing).",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {},
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
                "battery_capacity_kwh": {
                    "type": "number",
                    "description": "The total battery capacity of the electric vehicle in kilowatt-hours.",
                    "examples": [75.0],
                },
                "max_charging_power_ac": {
                    "type": "number",
                    "description": "The maximum charging power of the vehicle for AC charging in kilowatts.",
                    "examples": [11.0],
                },
                "max_charging_power_dc": {
                    "type": "number",
                    "description": "The maximum charging power of the vehicle for DC charging in kilowatts.",
                    "examples": [150.0],
                },
                "state_of_charge": {
                    "type": "integer",
                    "description": "The current state of charge of the electric vehicle in percentage.",
                    "examples": [80],
                },
                "remaining_range": {
                    "type": "string",
                    "description": "The estimated remaining driving range of the vehicle in kilometers. Calculated based on current power consumption.",
                    "examples": ["300 km"],
                },
            },
            "required": [
                "battery_capacity_kwh",
                "max_charging_power_ac",
                "max_charging_power_dc",
                "state_of_charge",
                "remaining_range",
            ],
            "additionalProperties": False,
        }
