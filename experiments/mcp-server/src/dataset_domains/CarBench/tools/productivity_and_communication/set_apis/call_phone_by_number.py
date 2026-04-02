import json
from typing import Any, Dict, List, Union

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.mock_data import car_va_data_manager
from dataset_domains.CarBench.tasks.task_config import task_config
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class CallPhoneByNumber(Tool):
    "Email Tool: sends an email with the specified message to the specified email adresses."

    @staticmethod
    def invoke(phone_number: str) -> str:
        """
        Args:

        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Contact information for the specified contact 'id's. Contact information includes name, phone number, and email.
            errors (dict): Error messages if the tool call was a "FAILURE".
        """
        response = {}
        vehicle_ctx = context_state.get()

        phone_numbers_called = vehicle_ctx.phone_numbers_called
        phone_numbers_called.append(phone_number)
        vehicle_ctx.update_state(phone_numbers_called=phone_numbers_called)
        response["status"] = "SUCCESS"
        response["result"] = {"phone_number_called": True}

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "call_phone_by_number",
                "description": "Phone Tool: calls the specified phone number.",
                "parameters": {
                    "type": "object",
                    "required": [
                        "phone_number",
                    ],
                    "properties": {
                        "phone_number": {
                            "type": "string",
                            "description": "The phone number to call.",
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
                "phone_number_called": {
                    "type": "boolean",
                    "description": "Indicates whether the specified phone number was successfully called. This output is always true if the operation succeeds.",
                    "examples": [True],
                }
            },
            "required": ["phone_number_called"],
            "additionalProperties": False,
        }
