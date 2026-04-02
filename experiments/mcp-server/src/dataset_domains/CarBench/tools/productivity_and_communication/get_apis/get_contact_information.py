import json
from typing import Any, Dict, List, Union

from dataset_domains.CarBench.mock_data import car_va_data_manager
from dataset_domains.CarBench.tools.helper_functions import (
    check_correct_id_format,
)
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class GetContactInformation(Tool):
    "Contact Information: gets the contact information for the specified contact 'id's. Contact information includes name, phone number, and email."

    @staticmethod
    def invoke(contact_ids: List[str]) -> str:
        """
        Args:
            contact_ids (list): List of contact 'id's to get the contact information for.
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Contact information for the specified contact 'id's. Contact information includes name, phone number, and email.
            errors (dict): Error messages if the tool call was a "FAILURE".
        """
        response = {}

        contact_information = {}
        for contact_id in contact_ids:
            if check_correct_id_format(contact_id, "contact") == False:
                response["status"] = "FAILURE"
                error_message = "GetContactInformation_001: Invalid contact_id format."
                tool_execution_errors_during_runtime.get().append(error_message)
                response["errors"] = {"GET_CONTACT_INFORMATION_001": error_message}
                return json.dumps(response)
            contact_data = car_va_data_manager.get_contact_information(contact_id)
            # contact_data.pop("id")
            contact_information[contact_id] = contact_data

        response["status"] = "SUCCESS"
        response["result"] = contact_information

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "get_contact_information",
                "description": "Contact Information: gets the contact information for the specified contact 'id's. Contact information includes name, phone number, and email.",
                "parameters": {
                    "type": "object",
                    "required": ["contact_ids"],
                    "properties": {
                        "contact_ids": {
                            "type": "array",
                            "description": "List of contact 'id's to get the contact information for.",
                            "items": {"type": "string", "description": "Contact 'id'."},
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
                # The result is a dictionary mapping contact_id to their contact info
                "result": {
                    "type": "object",
                    "description": "Dictionary mapping contact_id to their contact information.",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "object",
                                "properties": {
                                    "first_name": {
                                        "type": "string",
                                        "description": "The first name of the contact.",
                                        "examples": ["John"],
                                    },
                                    "last_name": {
                                        "type": "string",
                                        "description": "The last name of the contact.",
                                        "examples": ["Doe"],
                                    },
                                },
                                "required": ["first_name", "last_name"],
                                "description": "The name of the contact.",
                            },
                            "phone_number": {
                                "type": "string",
                                "description": "The phone number of the contact.",
                                "examples": ["+49 1234 567890"],
                            },
                            "email": {
                                "type": "string",
                                "description": "The email address of the contact.",
                                "examples": ["john.doe@yahoo.com"],
                            },
                        },
                        "required": ["name", "phone_number", "email"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["result"],
            "additionalProperties": False,
        }
