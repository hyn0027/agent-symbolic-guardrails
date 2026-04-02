import json
from typing import Any, Dict, Union

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.tool import Tool


class GetSeatHeatingLevel(Tool):
    "Vehicle Information: Get the level of seat heating in the different seat zones."

    @staticmethod
    def invoke() -> str:
        """
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Contains the level of seat heating in the different seat zones.
        """
        vehicle_ctx = context_state.get()
        response = {}

        response["status"] = "SUCCESS"
        response["result"] = {
            "seat_heating_driver": vehicle_ctx.seat_heating_driver,
            "seat_heating_passenger": vehicle_ctx.seat_heating_passenger,
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
                "name": "get_seat_heating_level",
                "description": "Vehicle Information: Get the level of seat heating in the different seat zones.",
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
                "seat_heating_driver": {
                    "type": "integer",
                    "description": "The heating level for the driver seat.",
                    "examples": [1],
                },
                "seat_heating_passenger": {
                    "type": "integer",
                    "description": "The heating level for the passenger seat.",
                    "examples": [1],
                },
            },
            "required": ["seat_heating_driver", "seat_heating_passenger"],
            "additionalProperties": False,
        }
