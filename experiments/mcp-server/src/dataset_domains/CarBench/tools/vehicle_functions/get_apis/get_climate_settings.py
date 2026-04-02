import json
from typing import Any, Dict, Union

from pydantic import BaseModel, Field

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.tool import Tool


class GetClimateSettings(Tool):
    "Vehicle Information: Get the climate settings inside the car including current fan speed, fan airflow direction, air conditioning status, air circulation mode, and window defrost status."

    @staticmethod
    def invoke() -> str:
        """
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS".
            result (dict): Contains the climate settings.
        """
        vehicle_ctx = context_state.get()
        response = {}
        response["status"] = "SUCCESS"
        response["result"] = {
            "fan_speed": vehicle_ctx.fan_speed,
            "fan_airflow_direction": vehicle_ctx.fan_airflow_direction.value,
            "air_conditioning": vehicle_ctx.air_conditioning,
            "air_circulation": vehicle_ctx.air_circulation.value,
            "window_front_defrost": vehicle_ctx.window_front_defrost,
            "window_rear_defrost": vehicle_ctx.window_rear_defrost,
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
                "name": "get_climate_settings",
                "description": "Vehicle Information: Get the climate settings inside the car including current fan speed, fan airflow direction, air conditioning status, air circulation mode, and window defrost status.",
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
                "fan_speed": {
                    "type": "integer",
                    "description": "The current climate fan speed setting.",
                    "examples": [3],
                },
                "fan_airflow_direction": {
                    "type": "string",
                    "description": "The active fan airflow direction as a string.",
                    "examples": ["FEET"],
                },
                "air_conditioning": {
                    "type": "boolean",
                    "description": "Indicates whether air conditioning is active.",
                    "examples": [True],
                },
                "air_circulation": {
                    "type": "string",
                    "description": "The current air circulation mode.",
                    "examples": ["AUTO"],
                },
                "window_front_defrost": {
                    "type": "boolean",
                    "description": "Status of the front window defrost.",
                    "examples": [False],
                },
                "window_rear_defrost": {
                    "type": "boolean",
                    "description": "Status of the rear window defrost.",
                    "examples": [False],
                },
            },
            "required": [
                "fan_speed",
                "fan_airflow_direction",
                "air_conditioning",
                "air_circulation",
                "window_front_defrost",
                "window_rear_defrost",
            ],
            "additionalProperties": False,
        }
