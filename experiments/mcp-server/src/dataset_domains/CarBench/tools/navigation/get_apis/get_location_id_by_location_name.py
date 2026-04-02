import json
from typing import Any, Dict, Optional

from dataset_domains.CarBench.mock_data import car_va_data_manager
from dataset_domains.CarBench.tools.navigation.helper_functions import (
    levenshtein_distance,
)
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class GetLocationIdByLocationName(Tool):
    """
    Location Information: Gets the location 'id' (e.g., 'loc_mun_1234') for a
    specified location or city name using fuzzy matching (Levenshtein distance).
    It specifically searches location names, not points of interest.
    """

    name = "get_location_id_by_name"  # Assign a name if needed

    @staticmethod
    def invoke(location: str) -> str:
        """
        Args:
            location_name_input (str): The location or city name to find the ID for.

        Returns:
            str: JSON string containing status, result (dict with 'id'), or errors.
        """
        response = {}

        # --- Check if DataManager is available ---
        if car_va_data_manager is None:
            response["status"] = "FAILURE"
            error_message = "GetLocationIdByLocationName_001: Core Data Manager failed to initialize."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_LOCATION_ID_BY_LOCATION_NAME_001": error_message}
            return json.dumps(response)

        # --- Input Validation ---
        if not location or not isinstance(location, str):
            response["status"] = "FAILURE"
            error_message = "GetLocationIdByLocationName_002: Invalid request - location_name_input must be a non-empty string."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_LOCATION_ID_BY_LOCATION_NAME_002": error_message}
            return json.dumps(response)

        # --- Access Cached Locations ---
        all_locations_dict = car_va_data_manager.locations
        if not all_locations_dict:
            response["status"] = "FAILURE"
            error_message = "GetLocationIdByLocationName_003: Data error - Location data is unavailable."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_LOCATION_ID_BY_LOCATION_NAME_003": error_message}
            return json.dumps(response)

        # --- Perform Fuzzy Matching ---
        search_name_lower = location.lower()
        best_match_location_data: Optional[Dict[str, Any]] = None
        min_distance = 3  # Set initial minimum distance threshold (allow distance <= 3)

        for location_data in all_locations_dict.values():
            current_name = location_data.get("name")
            if not current_name:  # Skip if a location somehow has no name
                continue

            current_name_lower = current_name.lower()
            distance = levenshtein_distance(search_name_lower, current_name_lower)

            if distance == 0:
                best_match_location_data = location_data
                min_distance = 0
                break  # Exit loop on perfect match

            if distance < min_distance:
                min_distance = distance
                best_match_location_data = location_data

        if best_match_location_data is None:  # No match found within distance <= 3
            response["status"] = "FAILURE"
            error_message = f"GetLocationIdByLocationName_004: Location not found - No close match found for '{location}'."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_LOCATION_ID_BY_LOCATION_NAME_004": error_message}
            return json.dumps(response)
        else:
            result_id = best_match_location_data.get("id")
            if not result_id:
                # Should not happen if cache structure is correct, but handle defensively
                error_message = "GetLocationIdByLocationName_005: Data integrity error - Matched location has no ID."
                tool_execution_errors_during_runtime.get().append(error_message)
                response["errors"] = {
                    "GET_LOCATION_ID_BY_LOCATION_NAME_005": error_message
                }
                return json.dumps(response)

            # --- Response ---
            response["status"] = "SUCCESS"
            response["result"] = {"id": result_id}
            return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "get_location_id_by_location_name",
                "description": "Location Information: gets the location 'id' for the specified location name or city name. It does not get the 'id' for points of interest.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["location"],
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location name to get the 'id' for.",
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
                    "description": "The location ID corresponding to the specified location name.",
                    "examples": ["loc_mun_1234"],
                }
            },
            "required": ["id"],
            "additionalProperties": False,
        }
