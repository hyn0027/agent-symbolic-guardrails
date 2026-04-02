import json
from typing import Any, Dict, Optional, Union

from dataset_domains.CarBench.context.fixed_context import fixed_context
from dataset_domains.CarBench.mock_data import car_va_data_manager
from dataset_domains.CarBench.tools.helper_functions import (
    check_correct_id_format,
)
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


def _get_charging_station_specs(
    charging_station_id: str, charging_station_plug_id: str
) -> Dict[str, Any]:
    poi_data = car_va_data_manager.pois
    for poi_id, poi_data in poi_data.items():
        if poi_id == charging_station_id:
            for plug in poi_data["charging_plugs"]:
                if plug["plug_id"] == charging_station_plug_id:
                    charging_station_specs = plug
                    return charging_station_specs
    return {}


class CalculateChargingSocByTime(Tool):
    "Charging Information: Calculates the reached state of charge when charging the car for the specified time. Calculation is based on charging plug specs, on car's maximum charging power for AC or DC charging, charging curve parameters."

    @staticmethod
    def invoke(
        charging_station_id,
        charging_station_plug_id,
        start_state_of_charge: int,
        charging_time: int,
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
        if not check_correct_id_format(charging_station_id, "poi_or_location"):
            response["status"] = "FAILURE"
            error_message = "CalculateChargingSocByTime_001: Invalid request - charging_station_id is not in correct format."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CALCULATE_CHARGING_SOC_BY_TIME_001": error_message}
            return json.dumps(response)
        if not check_correct_id_format(charging_station_plug_id, "charging_plug"):
            response["status"] = "FAILURE"
            error_message = "CalculateChargingSocByTime_002: Invalid request - charging_station_plug_id is not in correct format."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CALCULATE_CHARGING_SOC_BY_TIME_002": error_message}
            return json.dumps(response)

        if start_state_of_charge < 0 or start_state_of_charge > 100:
            response["status"] = "FAILURE"
            error_message = "CalculateChargingSocByTime_003: Invalid request - start_state_of_charge should be between 0 and 100."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CALCULATE_CHARGING_SOC_BY_TIME_003": error_message}
            return json.dumps(response)

        if charging_time < 0:
            response["status"] = "FAILURE"
            error_message = "CalculateChargingSocByTime_004: Invalid request - charging time should be greater than 0."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CALCULATE_CHARGING_SOC_BY_TIME_004": error_message}
            return json.dumps(response)

        charging_station_specs = _get_charging_station_specs(
            charging_station_id, charging_station_plug_id
        )
        if not charging_station_specs:
            response["status"] = "FAILURE"
            error_message = "CalculateChargingSocByTime_005: Invalid request - charging_station_plug_id not found."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CALCULATE_CHARGING_SOC_BY_TIME_005": error_message}
            return json.dumps(response)

        # --- Tool Execution ---
        if charging_station_specs["power_type"] == "AC":
            max_charging_power_car = fixed_ctx.max_charging_power_ac
        else:
            max_charging_power_car = fixed_ctx.max_charging_power_dc
        max_charging_power = min(
            max_charging_power_car, charging_station_specs["power_kw"]
        )
        charging_curve_parameters = fixed_ctx.charging_curve_parameters

        current_soc = start_state_of_charge
        for time_minute in range(charging_time):
            for i, soc_treshold in enumerate(
                charging_curve_parameters["soc_tresholds"]
            ):
                current_power = 0
                if current_soc <= soc_treshold:
                    current_power = (
                        charging_curve_parameters["power_percentages"][i] / 100
                    ) * max_charging_power
                    break
            energy_added = current_power / 60
            current_soc += (
                energy_added
                / (
                    fixed_ctx.battery_capacity_kwh
                    * (fixed_ctx.useable_battery_percentage / 100)
                )
            ) * 100

        # --- Response ---
        response["status"] = "SUCCESS"
        response["result"] = {
            f"soc_in_percent_after_charging_for_{charging_time}min": f"{round(current_soc, 0)} percent"
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
                "name": "calculate_charging_soc_by_time",
                "description": "Charging Information: Calculates the reached state of charge when charging the car for the specified time. Calculation is based on charging plug specs, on car's maximum charging power for AC or DC charging, charging curve parameters.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": [
                        "charging_station_id",
                        "charging_station_plug_id",
                        "start_state_of_charge",
                        "charging_time",
                    ],
                    "properties": {
                        "charging_station_id": {
                            "type": "string",
                            "description": "The ID of the charging station.",
                        },
                        "charging_station_plug_id": {
                            "type": "string",
                            "description": "The ID of the specific plug of the charging station where the car is connected to.",
                        },
                        "start_state_of_charge": {
                            "type": "integer",
                            "description": "The start state of charge of the electric vehicle (in percentage).",
                            "minimum": 0,
                            "maximum": 100,
                        },
                        "charging_time": {
                            "type": "integer",
                            "description": "The charging time in minutes.",
                            "minimum": 0,
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
                "soc_in_percent_after_charging_for_time_minutes": {
                    "type": "string",
                    "description": "The state of charge in percentage after charging for the specified time. Output present if charging_time was given.",
                    "examples": ["70 percent"],
                }
            },
            "required": ["soc_in_percent_after_charging_for_time_minutes"],
            "additionalProperties": False,
        }
