import json
from typing import Any, Dict, List, Optional, Union

from dataset_domains.CarBench.mock_data import car_va_data_manager
from dataset_domains.CarBench.tools.navigation.helper_functions import (
    levenshtein_distance,
)
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class GetContactIdByContactName(Tool):
    "Contact Information: gets the contact 'id' for the specified contact name."

    @staticmethod
    def invoke(
        contact_first_name: Optional[str] = None,
        contact_last_name: Optional[str] = None,
    ) -> str:
        """
        Args:
            contact_first_name (str, optional): The first name of the contact to get the 'id' for.
            contact_last_name (str, optional): The last name of the contact to get the 'id' for.
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): The matched ids.
            errors (dict): Error messages if the tool call was a "FAILURE".
        """
        response = {}

        # Validate at least one search parameter is provided
        if not contact_first_name and not contact_last_name:
            response["status"] = "FAILURE"
            error_message = "GetContactIdByContactName_001: At least one of contact_first_name or contact_last_name must be provided."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_CONTACT_ID_BY_CONTACT_NAME": error_message}
            return json.dumps(response)

        contact_data = car_va_data_manager.contacts
        matches = []

        # Normalize inputs
        first_name_query = contact_first_name.lower() if contact_first_name else ""
        last_name_query = contact_last_name.lower() if contact_last_name else ""

        # Prepare contacts for matching
        for contact_id, contact in contact_data.items():
            contact_first = contact["name"]["first_name"].lower()
            contact_last = contact["name"]["last_name"].lower()

            # Standard search - match components individually
            match_score = 0
            components_matched = 0

            if contact_first_name:
                first_distance = levenshtein_distance(first_name_query, contact_first)
                if (
                    first_distance <= 2
                ):  # Allow 3 as max distance for individual components
                    match_score += first_distance
                    components_matched += 1

            if contact_last_name:
                last_distance = levenshtein_distance(last_name_query, contact_last)
                if last_distance <= 2:
                    match_score += last_distance
                    components_matched += 1

            # Only consider matches where all provided components matched
            expected_components = sum(
                1 for x in [contact_first_name, contact_last_name] if x
            )
            if components_matched == expected_components:
                matches.append(
                    {
                        "id": contact["id"] if "id" in contact else contact_id,
                        "name": f"{contact_first} {contact_last}",
                        "distance": match_score,
                    }
                )

        # Sort by distance (closest matches first)
        matches.sort(key=lambda x: x["distance"])

        # Filter to only include perfect matches and close matches (distance <= 1)
        close_matches = [match for match in matches if match["distance"] <= 1]

        if not matches:
            response["status"] = "FAILURE"
            error_message = "GetContactIdByContactName_002: Invalid contact requested - contact not found."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_CONTACT_ID_BY_CONTACT_NAME": error_message}
        elif not close_matches:
            # Use the best match if no close matches found
            response["status"] = "SUCCESS"
            response["result"] = {"id": matches[0]["id"], "name": matches[0]["name"]}
        else:
            # Return all close matches with names
            response["status"] = "SUCCESS"
            response["result"] = {
                "matches": {match["id"]: match["name"] for match in close_matches}
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
                "name": "get_contact_id_by_contact_name",
                "description": "Contact Information: gets the contact 'id' for the specified contact name. You can search by first name, last name, or both.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": [],
                    "properties": {
                        "contact_first_name": {
                            "type": "string",
                            "description": "The first name of the contact to get the 'id' for.",
                        },
                        "contact_last_name": {
                            "type": "string",
                            "description": "The last name of the contact to get the 'id' for.",
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
                "id": {
                    "type": "string",
                    "description": "The contact ID associated with the matched contact name when there is a single match.",
                    "examples": ["con_1001"],
                },
                "name": {
                    "type": "string",
                    "description": "The full name of the matched contact when there is a single match.",
                    "examples": ["John Smith"],
                },
                "matches": {
                    "type": "object",
                    "description": "A mapping of contact IDs to names when multiple matches are found within a Levenshtein distance of 1.",
                    "additionalProperties": {
                        "type": "string",
                        "description": "Contact name",
                    },
                    "example": {"con_1001": "John Smith", "con_1002": "Jon Smith"},
                },
            },
            "additionalProperties": False,
        }
