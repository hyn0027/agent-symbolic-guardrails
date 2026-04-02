import json
from typing import Any, Dict, Literal, TypeAlias, Union

from pydantic import BaseModel, Field

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.tool import Tool


class SetFogLights(Tool):
    "Vehicle Control: Turns the fog lights outside the car on or off."

    # TODO: write set_fog_lights
    @staticmethod
    def invoke(on: bool) -> str:
        """
        Args:
            on (bool): True to turn on the fog lights, False to turn off the fog lights.
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
        """
        vehicle_ctx = context_state.get()
        response = {}

        response["status"] = "SUCCESS"
        response["result"] = {"on": on}  #
        vehicle_ctx.update_state(fog_lights=on)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "set_fog_lights",
                "description": "Vehicle Control: Turns the fog lights outside the car on or off.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["on"],
                    "properties": {
                        "on": {
                            "type": "boolean",
                            "description": "True to turn on the fog lights, False to turn off the fog lights.",
                        }
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
                "on": {
                    "type": "boolean",
                    "description": "Indicates whether the fog lights were turned on (true) or off (false).",
                    "examples": [True],
                }
            },
            "required": ["on"],
            "additionalProperties": False,
        }
