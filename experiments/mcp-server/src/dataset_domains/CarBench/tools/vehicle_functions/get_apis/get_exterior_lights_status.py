import json
from typing import Any, Dict, Union

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.tool import Tool


class GetExteriorLightsStatus(Tool):
    "Vehicle Information: Get the status of car exterior lights including headlights (low beam and high beam), and fog lights."

    @staticmethod
    def invoke() -> str:
        """
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Contains the status of fog lights, head lights low beams, and head lights high beams.
        """
        vehicle_ctx = context_state.get()
        response = {}
        response["status"] = "SUCCESS"
        response["result"] = {
            "fog_lights": vehicle_ctx.fog_lights,
            "head_lights_low_beams": vehicle_ctx.head_lights_low_beams,
            "head_lights_high_beams": vehicle_ctx.head_lights_high_beams,
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
                "name": "get_exterior_lights_status",
                "description": "Vehicle Information: Get the status of car exterior lights including headlights (low beam and high beam), and fog lights.",
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
                "fog_lights": {
                    "type": "boolean",
                    "description": "Status of the fog lights.",
                    "examples": [True],
                },
                "head_lights_low_beams": {
                    "type": "boolean",
                    "description": "Status of the head lights' low beams.",
                    "examples": [False],
                },
                "head_lights_high_beams": {
                    "type": "boolean",
                    "description": "Status of the head lights' high beams.",
                    "examples": [False],
                },
            },
            "required": [
                "fog_lights",
                "head_lights_low_beams",
                "head_lights_high_beams",
            ],
            "additionalProperties": False,
        }
