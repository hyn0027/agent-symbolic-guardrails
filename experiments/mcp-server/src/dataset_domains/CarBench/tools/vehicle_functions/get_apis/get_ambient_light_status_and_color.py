import json
from typing import Any, Dict, Union

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.tool import Tool


class GetAmbientLightStatusAndColor(Tool):
    "Vehicle Information: Get the status and color of the car ambient light (the soft, decorative lighting inside the cabin). Also referred to as 'surrounding light'."

    @staticmethod
    def invoke() -> str:
        """
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Contains the status and color of the car ambient light.
        """
        vehicle_ctx = context_state.get()
        response = {}

        ambient_light_status = vehicle_ctx.ambient_light.value
        response["status"] = "SUCCESS"
        response["result"] = {"ambient_light": ambient_light_status}

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "get_ambient_light_status_and_color",
                "description": "Vehicle Information: Get the status and color of the car ambient light (the soft, decorative lighting inside the cabin). Also referred to as 'surrounding light'.",
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
                "ambient_light": {
                    "type": "string",
                    "description": "The current status and color of the ambient light.",
                    "examples": ["BLUE"],
                }
            },
            "required": ["ambient_light"],
            "additionalProperties": False,
        }
