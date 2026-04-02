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
    charging_station_id, charging_station_plug_id: str
) -> Dict[str, Any]:
    pois = car_va_data_manager.pois
    for poi_id, poi_data in pois.items():
        if poi_id == charging_station_id:
            for plug in poi_data["charging_plugs"]:
                if plug["plug_id"] == charging_station_plug_id:
                    charging_station_specs = plug
                    return charging_station_specs
    return {}


class CalculateChargingTimeBySoc(Tool):
    "Charging Information: Calculates the charging time for charging from an start state of charge to a target state of charge of the car based charging plug specs, on car's maximum charging power for AC or DC charging, charging curve parameters."

    @staticmethod
    def invoke(
        charging_station_id,
        charging_station_plug_id,
        start_state_of_charge: int,
        target_state_of_charge: Optional[int] = None,
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
            error_message = "CalculateChargingTimeBySoc_001: Invalid request - charging_station_id is not in correct format."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CALCULATE_CHARGING_TIME_001": error_message}
            return json.dumps(response)
        if not check_correct_id_format(charging_station_plug_id, "charging_plug"):
            response["status"] = "FAILURE"
            error_message = "CalculateChargingTimeBySoc_002: Invalid request - charging_station_plug_id is not in correct format."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CALCULATE_CHARGING_TIME_002": error_message}
            return json.dumps(response)

        if start_state_of_charge < 0 or start_state_of_charge > 100:
            response["status"] = "FAILURE"
            error_message = "CalculateChargingTimeBySoc_003: Invalid request - start_state_of_charge should be between 0 and 100."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CALCULATE_CHARGING_TIME_003": error_message}
            return json.dumps(response)

        if target_state_of_charge is not None and (
            target_state_of_charge < 0 or target_state_of_charge > 100
        ):
            response["status"] = "FAILURE"
            error_message = "CalculateChargingTimeBySoc_004: Invalid request - target_state_of_charge should be between 0 and 100."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CALCULATE_CHARGING_TIME_004": error_message}
            return json.dumps(response)

        if (
            target_state_of_charge is not None
            and start_state_of_charge > target_state_of_charge
        ):
            response["status"] = "FAILURE"
            error_message = "CalculateChargingTimeBySoc_005: Invalid request - start_state_of_charge cannot be greater than target_state_of_charge."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CALCULATE_CHARGING_TIME_005": error_message}
            return json.dumps(response)

        charging_station_specs = _get_charging_station_specs(
            charging_station_id, charging_station_plug_id
        )
        if not charging_station_specs:
            response["status"] = "FAILURE"
            error_message = "CalculateChargingTimeBySoc_006: Invalid request - charging_station_plug_id not found."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CALCULATE_CHARGING_TIME_006": error_message}
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

        target_soc = [target_state_of_charge] if target_state_of_charge else [80, 100]
        total_times = []
        for target_soc_ in target_soc:
            # simulate 1-minute intervals
            current_soc = start_state_of_charge
            total_time_minutes = 0
            while current_soc < (target_soc_ - 1):
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
                total_time_minutes += 1
            total_times.append(total_time_minutes)

        # --- Response ---
        if target_state_of_charge is None:
            response["status"] = "SUCCESS"
            response["result"] = {
                f"time_from_{start_state_of_charge}_until_80_percent_soc": f"{total_times[0]}min",
                f"time_from_{start_state_of_charge}_until_100_percent_soc": f"{total_times[1]}min",
            }
            return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {
            f"time_from_{start_state_of_charge}_until_{target_state_of_charge}_percent_soc": f"{total_times[0]}min"
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
                "name": "calculate_charging_time_by_soc",
                "description": "Charging Information: Calculates the charging time for charging from an start state of charge to a target state of charge of the car based charging plug specs, on car's maximum charging power for AC or DC charging, charging curve parameters.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": [
                        "charging_station_id",
                        "charging_station_plug_id",
                        "start_state_of_charge",
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
                        "target_state_of_charge": {
                            "type": "integer",
                            "description": "The target state of charge of the electric vehicle (in percentage). If not specified, time until 80 percent and 100 percent is given.",
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
                "time_from_start_state_of_charge_until_80_percent_soc": {
                    "type": "string",
                    "description": "The time in minutes from the start state of charge to 80 percent state of charge. Output present if target_state_of_charge was not given.",
                    "examples": ["15min"],
                },
                "time_from_start_state_of_charge_until_100_percent_soc": {
                    "type": "string",
                    "description": "The time in minutes from the start state of charge to 100 percent state of charge. Output present if target_state_of_charge was not given.",
                    "examples": ["15min"],
                },
                "time_from_start_state_of_charge_until_target_state_of_charge_percent_soc": {
                    "type": "string",
                    "description": "The time in minutes from the start state of charge to the specified target state of charge. Output present if target_state_of_charge was given.",
                    "examples": ["15min"],
                },
            },
            "required": [],
            "additionalProperties": False,
        }
