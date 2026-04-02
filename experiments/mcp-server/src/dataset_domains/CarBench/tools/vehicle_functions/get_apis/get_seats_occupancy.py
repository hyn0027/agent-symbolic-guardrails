import json
from typing import Any, Dict, Union

from dataset_domains.CarBench.context.fixed_context import fixed_context
from dataset_domains.CarBench.tools.tool import Tool


class GetSeatsOccupancy(Tool):
    "Vehicle Information: Get the occupancy of seats inside the car."

    @staticmethod
    def invoke() -> str:
        """
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Contains the occupancy status of the seats inside the car.
        """
        fixed_ctx = fixed_context.get()
        response = {}

        seats_occupied = fixed_ctx.seats_occupied
        response["status"] = "SUCCESS"
        response["result"] = {"seats_occupied": seats_occupied}

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "get_seats_occupancy",
                "description": "Vehicle Information: Get the occupancy of seats inside the car.",
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
                "seats_occupied": {
                    "type": "object",
                    "description": "A dictionary mapping each seat to its occupancy status.",
                    "additionalProperties": {
                        "type": "boolean",
                        "description": "True if the seat is occupied, false otherwise.",
                        "examples": [True],
                    },
                    "examples": [
                        {
                            "driver": True,
                            "passenger": False,
                            "driver_rear": False,
                            "passenger_rear": False,
                        }
                    ],
                }
            },
            "required": ["seats_occupied"],
            "additionalProperties": False,
        }
