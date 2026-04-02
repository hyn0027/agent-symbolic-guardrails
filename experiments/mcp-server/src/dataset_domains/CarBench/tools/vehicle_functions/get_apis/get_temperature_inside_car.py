import json
from typing import Any, Dict

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.tool import Tool


class GetTemperatureInsideCar(Tool):
    "Vehicle Information: Get the temperature in the different seat zones inside the car."

    @staticmethod
    def invoke() -> str:
        """
        Returns:
             status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
             result (dict): Contains the temperature in the different seat zones inside the car.
        """
        vehicle_ctx = context_state.get()
        response = {}
        response["status"] = "SUCCESS"
        response["result"] = {
            "climate_temperature_driver": vehicle_ctx.climate_temperature_driver,
            "climate_temperature_passenger": vehicle_ctx.climate_temperature_passenger,
            "temperature_unit": "Celsius",
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
                "name": "get_temperature_inside_car",
                "description": "Vehicle Information: Get the temperature in the different seat zones inside the car.",
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
                "climate_temperature_driver": {
                    "type": "number",
                    "description": "The temperature setting for the driver's zone in Celsius.",
                    "examples": [20],
                },
                "climate_temperature_passenger": {
                    "type": "number",
                    "description": "The temperature setting for the passenger's zone in Celsius.",
                    "examples": [20],
                },
                "temperature_unit": {
                    "type": "string",
                    "description": "The unit for the temperature measurement.",
                    "examples": ["Celsius"],
                },
            },
            "required": [
                "climate_temperature_driver",
                "climate_temperature_passenger",
                "temperature_unit",
            ],
            "additionalProperties": False,
        }
