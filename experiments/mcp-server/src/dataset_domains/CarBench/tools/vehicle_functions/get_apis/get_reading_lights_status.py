import json
from typing import Any, Dict, Union

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.tool import Tool


class GetReadingLightsStatus(Tool):
    "Vehicle Information: Get the status of car reading lights (interior)."

    @staticmethod
    def invoke() -> str:
        """
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS".
            result (dict): Contains the status of reading lights for driver, passenger, driver rear, and passenger rear.
        """
        vehicle_ctx = context_state.get()
        response = {}
        response["status"] = "SUCCESS"
        response["result"] = {
            "reading_light_driver": vehicle_ctx.reading_light_driver,
            "reading_light_passenger": vehicle_ctx.reading_light_passenger,
            "reading_light_driver_rear": vehicle_ctx.reading_light_driver_rear,
            "reading_light_passenger_rear": vehicle_ctx.reading_light_passenger_rear,
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
                "name": "get_reading_lights_status",
                "description": "Vehicle Information: Get the status of car reading lights (interior).",
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
                "reading_light_driver": {
                    "type": "boolean",
                    "description": "Status of the driver's reading light.",
                    "examples": [True],
                },
                "reading_light_passenger": {
                    "type": "boolean",
                    "description": "Status of the passenger's reading light.",
                    "examples": [False],
                },
                "reading_light_driver_rear": {
                    "type": "boolean",
                    "description": "Status of the driver rear reading light.",
                    "examples": [False],
                },
                "reading_light_passenger_rear": {
                    "type": "boolean",
                    "description": "Status of the passenger rear reading light.",
                    "examples": [False],
                },
            },
            "required": [
                "reading_light_driver",
                "reading_light_passenger",
                "reading_light_driver_rear",
                "reading_light_passenger_rear",
            ],
            "additionalProperties": False,
        }
