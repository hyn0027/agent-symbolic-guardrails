import json
from typing import Any, Dict, Union

from pydantic import BaseModel, Field

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.tool import Tool


class GetSunroofAndSunshadePosition(Tool):
    "Vehicle Information: Get information about the position of the car sunroof and sunshade."

    @staticmethod
    def invoke() -> str:
        """
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Contains the position of the car sunroof and sunshade.
        """
        vehicle_ctx = context_state.get()
        response = {}

        sunroof_position = vehicle_ctx.sunroof_position
        sunshade_position = vehicle_ctx.sunshade_position

        response["status"] = "SUCCESS"
        response["result"] = {
            "description": "Current positions of sunroof and sunshade",
            "sunroof_position": sunroof_position,
            "sunshade_position": sunshade_position,
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
                "name": "get_sunroof_and_sunshade_position",
                "description": "Vehicle Information: Get information about the position of the car sunroof and sunshade.",
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
                "description": {
                    "type": "string",
                    "description": "A description of the sunroof and sunshade positions.",
                    "examples": ["Current positions of sunroof and sunshade"],
                },
                "sunroof_position": {
                    "type": "integer",
                    "description": "The current open percentage of the sunroof (0 to 100).",
                    "examples": [50],
                },
                "sunshade_position": {
                    "type": "integer",
                    "description": "The current open percentage of the sunshade (0 to 100).",
                    "examples": [30],
                },
            },
            "required": ["description", "sunroof_position", "sunshade_position"],
            "additionalProperties": False,
        }
