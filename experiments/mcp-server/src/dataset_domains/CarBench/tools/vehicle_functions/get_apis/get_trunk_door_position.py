import json
from typing import Any, Dict, Union

from pydantic import BaseModel

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.tool import Tool


class GetTrunkDoorPosition(Tool):
    "Vehicle Information: Get information about the position of the car trunk door."

    @staticmethod
    def invoke() -> str:
        """
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Contains the trunk door position.
        """
        vehicle_ctx = context_state.get()
        response = {}

        trunk_door_position = vehicle_ctx.trunk_door_position

        response["status"] = "SUCCESS"
        response["result"] = {"trunk_door_position": trunk_door_position}
        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "get_trunk_door_position",
                "description": "Vehicle Information: Get information about the position of the car trunk door.",
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
                "trunk_door_position": {
                    "type": "string",
                    "description": "The current position of the trunk door, for example 'open' or 'closed'.",
                    "examples": ["closed"],
                }
            },
            "required": ["trunk_door_position"],
            "additionalProperties": False,
        }
