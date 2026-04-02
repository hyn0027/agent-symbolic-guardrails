import json
from typing import Any, Dict, Literal, TypeAlias, Union

from pydantic import BaseModel, Field

from dataset_domains.CarBench.context.fixed_context import fixed_context
from dataset_domains.CarBench.tools.tool import Tool


class GetFuelInformation(Tool):
    "Vehicle Information: Get information about the fuel type, fuel consumption, and remaining fuel."

    @staticmethod
    def invoke() -> str:
        """
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Contains the fuel type, fuel consumption, and remaining fuel.
        """
        fixed_ctx = fixed_context.get()
        response = {}

        response["status"] = "SUCCESS"
        response["result"] = {
            "fuel_type": fixed_ctx.fuel_type,
            "regular_fuel_consumption": fixed_ctx.regular_fuel_consumption,
            "fuel_consumption_unit": "L/100km",
            "remaining_fuel": f"{fixed_ctx.remaining_fuel} L",
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
                "name": "get_fuel_information",
                "description": "Vehicle Information: Get information about the fuel type, fuel consumption, and remaining fuel.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
        }

    # @staticmethod
    # def get_output_info() -> Dict[str, Any]:
    #     """
    #     Output variable description
    #     """
    #     return {
    #         "type": "object",
    #         "properties": {
    #             "fuel_type": {
    #                 "type": "string",
    #                 "description": "The fuel type used by the car.",
    #                 "examples": ["gasoline"]
    #             },
    #             "regular_fuel_consumption": {
    #                 "type": "number",
    #                 "description": "Fuel consumption in liters per 100 km.",
    #                 "examples": [8]
    #             },
    #             "fuel_consumption_unit": {
    #                 "type": "string",
    #                 "description": "The unit of fuel consumption.",
    #                 "examples": ["L/100km"]
    #             },
    #             "remaining_fuel": {
    #                 "type": "string",
    #                 "description": "The remaining fuel amount with unit.",
    #                 "examples": ["50 L"]
    #             }
    #         },
    #         "required": ["fuel_type", "regular_fuel_consumption", "fuel_consumption_unit", "remaining_fuel"],
    #         "additionalProperties": False
    #     }
