import json
from typing import Any, Dict, Union

from pydantic import BaseModel, Field

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class SetSeatHeating(Tool):
    "Vehicle Climate Control: Sets the seat heating inside the car to the specified seat zones."

    @staticmethod
    def invoke(level: int, seat_zone: str) -> str:
        """
        Args:
            level (int): The level to set the seat heating to, ranging from 0 to 3.
            seat_zone (str): The seat zone to set the seat heating to, can be "ALL_ZONES", "DRIVER", or "PASSENGER".
        Returns:
            status (str): Indicates if the tool call was an "SUCCESS" or "FAILURE".
            level (int): The level to which the seat heating was set.
            seat_zone (str): The seat zone to which the seat heating was applied.
        """
        vehicle_ctx = context_state.get()
        response = {}

        valid_seat_zone = ["ALL_ZONES", "DRIVER", "PASSENGER"]
        # Check for Errors
        if level < 0 or level > 3:
            response["status"] = "FAILURE"
            error_message = "SetSeatHeating_001: Invalid level requested - only values between 0 and 3 are allowed."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SET_SEAT_HEATING_001": error_message}
            return json.dumps(response)

        if seat_zone not in valid_seat_zone:
            response["status"] = "FAILURE"
            error_message = "SetSeatHeating_002: Invalid seat zone requested - choose one of ALL_ZONES, DRIVER, PASSENGER."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SET_SEAT_HEATING_002": error_message}
            return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {"level": level, "seat_zone": seat_zone}
        if seat_zone == "ALL_ZONES":
            vehicle_ctx.update_state(
                seat_heating_driver=level, seat_heating_passenger=level
            )
        elif seat_zone == "DRIVER":
            vehicle_ctx.update_state(seat_heating_driver=level)
        elif seat_zone == "PASSENGER":
            vehicle_ctx.update_state(seat_heating_passenger=level)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """
        return {
            "type": "function",
            "function": {
                "name": "set_seat_heating",
                "description": "Vehicle Climate Control: Sets the seat heating inside the car to the specified seat zones.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["level", "seat_zone"],
                    "properties": {
                        "level": {
                            "type": "number",
                            "description": "The level to set the seat heating to.",
                            "multipleOf": 1,
                            "minimum": 0,
                            "maximum": 3,
                        },
                        "seat_zone": {
                            "type": "string",
                            "description": "The seat zone to set the seat heating to.",
                            "enum": ["ALL_ZONES", "DRIVER", "PASSENGER"],
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
                "level": {
                    "type": "integer",
                    "description": "The heating level set for the specified seat zone, ranging from 0 (off) to 3 (maximum).",
                    "examples": [2],
                },
                "seat_zone": {
                    "type": "string",
                    "description": "The seat zone that was affected by the heating adjustment.",
                    "examples": ["DRIVER"],
                },
            },
            "required": ["level", "seat_zone"],
            "additionalProperties": False,
        }
