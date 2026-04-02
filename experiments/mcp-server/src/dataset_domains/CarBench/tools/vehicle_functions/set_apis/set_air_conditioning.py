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


class SetAirConditioning(Tool):
    "Vehicle Climate Control: Turns on or off the air conditioning (AC) inside the car."

    # TODO: write set_air_conditioning
    @staticmethod
    def invoke(on: bool) -> str:
        """
        Args:
            on (bool): True to turn on the air conditioning, False to turn off the air conditioning.
        Returns:
            status (str): Indicates if the tool call was an "SUCCESS" or "FAILURE".
            on (bool): The state of the air conditioning after the operation.
        """
        vehicle_ctx = context_state.get()
        response = {}
        # no errors yet for SetAirConditioning

        response["status"] = "SUCCESS"
        response["result"] = {"on": on}
        vehicle_ctx.update_state(air_conditioning=on)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """
        return {
            "type": "function",
            "function": {
                "name": "set_air_conditioning",
                "description": "Vehicle Climate Control: Turns on or off the air conditioning (AC) inside the car.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["on"],
                    "properties": {
                        "on": {
                            "type": "boolean",
                            "description": "True to turn on the air conditioning, False to turn off the air conditioning.",
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
                    "description": "Indicates the state of the air conditioning after the operation.",
                    "examples": [True],
                }
            },
            "required": ["on"],
            "additionalProperties": False,
        }
