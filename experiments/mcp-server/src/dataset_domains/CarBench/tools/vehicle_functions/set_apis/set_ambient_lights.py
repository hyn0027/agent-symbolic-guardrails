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


class SetAmbientLights(Tool):
    "Vehicle Control: Turns the ambient light inside the car on including the color or off."

    # TODO: write set_ambient_lights
    @staticmethod
    def invoke(on: bool, lightcolor: str) -> str:
        """
        Args:
            on (bool): True to turn on the specified ambient light, False to turn off the ambient light.
            lightcolor (str): The color of the ambient light, None if the ambient light is turned off.
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
        """
        vehicle_ctx = context_state.get()
        response = {}
        valid_colors = [
            "RED",
            "GREEN",
            "BLUE",
            "YELLOW",
            "WHITE",
            "PINK",
            "ORANGE",
            "PURPLE",
            "CYAN",
            "NONE",
        ]
        # Check for Errors

        if lightcolor not in valid_colors:
            response["status"] = "FAILURE"
            error_message = "SetAmbientLights_001: Invalid color requested - choose one of RED, GREEN, BLUE, YELLOW, WHITE, PINK, ORANGE, PURPLE, CYAN, NONE."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SET_AMBIENT_LIGHT_001": error_message}
            return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {"on": on, "lightcolor": lightcolor}
        if (not on) or (lightcolor == "NONE"):
            vehicle_ctx.update_state(ambient_light="OFF")
        else:
            vehicle_ctx.update_state(ambient_light=lightcolor)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "set_ambient_lights",
                "description": "Vehicle Control: Turns the ambient light inside the car on (including the color) or off. Ambient light is the soft, decorative lighting inside the cabin, also referred to as 'surrounding light.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["on", "lightcolor"],
                    "properties": {
                        "on": {
                            "type": "boolean",
                            "description": "True to turn on the specified ambient light, False to turn off the ambient light.",
                        },
                        "lightcolor": {
                            "type": "string",
                            "description": "The color of the ambient light, None if the ambient light is turned off.",
                            "enum": [
                                "RED",
                                "GREEN",
                                "BLUE",
                                "YELLOW",
                                "WHITE",
                                "PINK",
                                "ORANGE",
                                "PURPLE",
                                "CYAN",
                                "NONE",
                            ],
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
                "on": {
                    "type": "boolean",
                    "description": "Indicates whether the ambient light was turned on.",
                    "examples": [True],
                },
                "lightcolor": {
                    "type": "string",
                    "description": "The color of the ambient light as set. This field is always present; if the light is turned off, it is typically set to 'NONE'.",
                    "examples": ["BLUE"],
                },
            },
            "required": ["on", "lightcolor"],
            "additionalProperties": False,
        }
