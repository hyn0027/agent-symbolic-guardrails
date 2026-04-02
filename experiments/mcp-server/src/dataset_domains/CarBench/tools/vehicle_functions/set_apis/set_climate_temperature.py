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


class SetClimateTemperature(Tool):
    "Vehicle Climate Control: Sets the climate inside the car to the specified temperature in the specified seat zones."

    @staticmethod
    def invoke(temperature: float, seat_zone: str) -> str:
        """
        Args:
            temperature (float): Sets the temperature of the AC inside the car in degree Celsius. Must be explicitly stated by the driver.
            seat_zone (str): The seat zone to set the temperature.
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
        """
        vehicle_ctx = context_state.get()
        response = {}

        valid_seat_zone = ["ALL_ZONES", "DRIVER", "PASSENGER"]
        # Check for Errors
        if temperature < 0 or temperature > 100:
            response["status"] = "FAILURE"
            error_message = "SetClimateTemperature_001: The specified temperature is not available - only values between 16 degree celcius and 28 degree celcius are allowed."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SET_CLIMATE_TEMPERATURE_001": error_message}
            return json.dumps(response)
        elif seat_zone not in valid_seat_zone:
            response["status"] = "FAILURE"
            error_message = "SetClimateTemperature_002: Invalid seat zone requested - choose one of ALL_ZONES, DRIVER, PASSENGER."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SET_CLIMATE_TEMPERATURE_002": error_message}
            return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {"temperature": temperature, "seat_zone": seat_zone}
        if seat_zone == "ALL_ZONES":
            vehicle_ctx.update_state(
                climate_temperature_driver=temperature,
                climate_temperature_passenger=temperature,
            )
        elif seat_zone == "DRIVER":
            vehicle_ctx.update_state(climate_temperature_driver=temperature)
        elif seat_zone == "PASSENGER":
            vehicle_ctx.update_state(climate_temperature_passenger=temperature)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "set_climate_temperature",
                "description": "Vehicle Climate Control: Sets the climate inside the car to the specified temperature in the specified seat zones.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["temperature", "seat_zone"],
                    "properties": {
                        "temperature": {
                            "type": "number",
                            "description": "Sets the temperature of the AC inside the car in degree Celsius. Must be explicitly stated by the driver.",
                            "multipleOf": 0.5,
                            "minimum": 16,
                            "maximum": 28,
                        },
                        "seat_zone": {
                            "type": "string",
                            "description": "The seat zone to set the temperature.",
                            "enum": ["ALL_ZONES", "DRIVER", "PASSENGER"],
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
                "temperature": {
                    "type": "number",
                    "description": "The climate temperature set in Celsius.",
                    "examples": [22.5],
                },
                "seat_zone": {
                    "type": "string",
                    "description": "The seat zone to which the temperature was applied.",
                    "examples": ["DRIVER"],
                },
            },
            "required": ["temperature", "seat_zone"],
            "additionalProperties": False,
        }
