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


class SendEmail(Tool):
    "Email Tool: sends an email with the specified message to the specified email adresses."

    @staticmethod
    def invoke(content_message: str, email_addresses: List[str]) -> str:
        """
        Args:

        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Contact information for the specified contact 'id's. Contact information includes name, phone number, and email.
            errors (dict): Error messages if the tool call was a "FAILURE".
        """
        response = {}
        vehicle_ctx = context_state.get()

        email_addresses_sent_mail_to = vehicle_ctx.email_addresses_sent_mail_to
        contact_information = {}
        for email in email_addresses:
            if not car_va_data_manager.check_if_email_in_contacts(email):
                response["status"] = "FAILURE"
                error_message = f"SendEmail_001: Invalid email address {email} - not found in contacts"
                tool_execution_errors_during_runtime.get().append(error_message)
                response["errors"] = {"SEND_EMAIL_001": error_message}
                return json.dumps(response)
            email_addresses_sent_mail_to.append(email)

        vehicle_ctx.update_state(
            email_addresses_sent_mail_to=email_addresses_sent_mail_to
        )
        response["status"] = "SUCCESS"
        response["result"] = {"email_sent": True}

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "send_email",
                "description": "REQUIRES_CONFIRMATION, Email Tool: sends an email with the specified message to the specified email adresses.",
                "parameters": {
                    "type": "object",
                    "required": ["content_message", "email_addresses"],
                    "properties": {
                        "content_message": {
                            "type": "string",
                            "description": "The content of the email message which is sent. Generate a suitable email message based on the user request if the user does not explicitely provide one. If there is no request about the content ask the user for it.",
                        },
                        "email_addresses": {
                            "type": "array",
                            "description": "List of email adresses to send the email to.",
                            "items": {
                                "type": "string",
                                "description": "Email adress, f.e. joe@gmail.com.",
                            },
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
                "email_sent": {
                    "type": "boolean",
                    "description": "Indicates whether the email was successfully sent to all specified email addresses. This field is always present and true if the operation succeeds.",
                    "examples": [True],
                }
            },
            "required": ["email_sent"],
            "additionalProperties": False,
        }
