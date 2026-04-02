import json
from typing import Any, Dict, List, Optional

from dataset_domains.CarBench.mock_data import car_va_data_manager
from dataset_domains.CarBench.tools.helper_functions import (
    check_correct_id_format,
)
from dataset_domains.CarBench.policy_evaluator import policy_errors_during_runtime
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class GetRoutes(Tool):
    """
    Searches for available route alternatives between a specified start point
    (Location or POI) and a destination point (Location or POI).
    Note: Routes between two POIs (POI -> POI) are not supported.
    """

    @staticmethod
    def invoke(start_id: str, destination_id: str) -> str:
        """
        Args:
            start_id (str): The ID of the starting location ('loc_...') or POI ('poi_...').
            destination_id (str): The ID of the destination location ('loc_...') or POI ('poi_...').

        Returns:
            str: JSON string containing status, result (list of route alternatives), or errors.
        """
        response = {}

        # --- Validate Input IDs ---
        if not check_correct_id_format(start_id, "poi_or_location"):
            response["status"] = "FAILURE"
            error_message = f"GetRoutes_001: Invalid request - Invalid start_id format '{start_id}'."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_ROUTES_001": error_message}
            return json.dumps(response)

        if not check_correct_id_format(destination_id, "poi_or_location"):
            response["status"] = "FAILURE"
            error_message = f"GetRoutes_002: Invalid request - Invalid destination_id format '{destination_id}'."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_ROUTES_002": error_message}
            return json.dumps(response)

        # --- Determine Start/Destination Types ---
        start_is_poi = start_id.startswith("poi_")
        start_is_loc = start_id.startswith("loc_")
        dest_is_poi = destination_id.startswith("poi_")
        dest_is_loc = destination_id.startswith("loc_")

        # --- Check for Unsupported POI -> POI Routes ---
        if start_is_poi and dest_is_poi:
            response["status"] = "FAILURE"
            error_message = "GetRoutes_003: Invalid request - Routes between two POIs are not supported."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_ROUTES_003": error_message}
            # Log policy error if needed
            # policy_errors_during_runtime.get().append(f"TECH-AUT-POL:011: {response['errors']['GET_ROUTES_003']}")
            return json.dumps(response)

        # --- Fetch Routes using DataManager based on types ---
        routes_list: List[Dict[str, Any]] = []  # Initialize empty list
        error_key = "GET_ROUTES_ERR"  # Default error key
        not_found_message = ""

        try:
            if start_is_loc and dest_is_loc:
                # Location -> Location search
                error_key = "GET_ROUTES_004"
                not_found_message = f"No routes found between location '{start_id}' and location '{destination_id}'."
                # print(
                    # f"DEBUG: Searching Loc->Loc routes: {start_id} -> {destination_id}"
                # )
                routes_list = car_va_data_manager.get_routes_location_to_location(
                    start_id, destination_id
                )

            elif start_is_loc and dest_is_poi:
                # Location -> POI search
                error_key = "GET_ROUTES_005"
                not_found_message = f"No routes found between location '{start_id}' and POI '{destination_id}'."
                # print(
                    # f"DEBUG: Searching Loc->POI routes: {start_id} -> {destination_id}"
                # )
                routes_list = car_va_data_manager.get_routes_location_to_poi(
                    start_id, destination_id
                )

            elif start_is_poi and dest_is_loc:
                # POI -> Location search (using the new DataManager method)
                error_key = "GET_ROUTES_006"
                not_found_message = f"No routes found between POI '{start_id}' and location '{destination_id}'."
                # print(
                    # f"DEBUG: Searching POI->Loc routes: {start_id} -> {destination_id}"
                # )
                routes_list = car_va_data_manager.get_routes_poi_to_location(
                    start_id, destination_id
                )

            else:
                # Should not happen due to POI->POI check, but handle defensively
                error_message = "GetRoutes_007: Internal error - Unknown combination of start/destination types."
                tool_execution_errors_during_runtime.get().append(error_message)
                response["errors"] = {"GET_ROUTES_007": error_message}
                return json.dumps(response)

            # Check if the search returned any routes
            if not routes_list:
                response["status"] = "FAILURE"
                error_message = f"GetRoutes_008: Internal error - Unknown combination of start/destination types."
                tool_execution_errors_during_runtime.get().append(error_message)
                response["errors"] = {"GET_ROUTES_008": error_message}
                response["errors"] = {error_key: not_found_message}
                return json.dumps(response)

        except Exception as e:
            # Catch unexpected errors during DataManager access
            # print(
                # f"ERROR during route search ({start_id} -> {destination_id}): {e}"
            # )  # Log the error
            response["status"] = "FAILURE"
            error_message = f"GetRoutes_009: An unexpected error occurred while fetching routes: {e}"
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_ROUTES_009": error_message}
            return json.dumps(response)

        # --- Success ---
        response["status"] = "SUCCESS"
        # The result is the list of found route alternative dictionaries
        response["result"] = {"routes": routes_list}

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "get_routes_from_start_to_destination",
                "description": "Routes information: gets the fastest route (plus alternative routes if existent) for the car between start and destination. Each route information includes name_via, distance in km, duration in hours and minutes, arrival time, road types (highway, urban, country roads, includes toll roads), and an route alias (first, second, third; additionaly fastest, shortest). Routes can be requested between locations or between a location and a point of interest.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["start_id", "destination_id"],
                    "properties": {
                        "start_id": {
                            "type": "string",
                            "description": "The starting point of the route. The starting point has to be the location 'id' or a points of interest 'id'.",
                        },
                        "destination_id": {
                            "type": "string",
                            "description": "The destination point of the route. The destination point has to be the location 'id' or a points of interest 'id'.",
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
                "routes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "route_id": {
                                "type": "string",
                                "description": "The ID of the route.",
                                "examples": ["rll_mun_erf_9149"],
                            },
                            "start_id": {
                                "type": "string",
                                "description": "ID of the starting point of the route.",
                                "examples": ["loc_mun_9995"],
                            },
                            "destination_id": {
                                "type": "string",
                                "description": "ID of the destination point of the route.",
                                "examples": ["loc_erf_4101"],
                            },
                            "name_via": {
                                "type": "string",
                                "description": "Name of the route via streets.",
                                "examples": ["K152, K277, K88"],
                            },
                            "distance_km": {
                                "type": "number",
                                "description": "Distance of the route in kilometers.",
                                "examples": [15.5],
                            },
                            "duration_hours": {
                                "type": "number",
                                "description": "Estimated duration of the route in hours.",
                                "examples": [1],
                            },
                            "duration_minutes": {
                                "type": "number",
                                "description": "Estimated duration of the route in minutes.",
                                "examples": [30],
                            },
                            "road_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Types of roads included in the route (e.g., highway, urban, country roads).",
                                "examples": [["highway", "urban"]],
                            },
                            "includes_toll": {
                                "type": "boolean",
                                "description": "Indicates if the route includes toll roads.",
                                "examples": [True],
                            },
                            "alias": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Aliases for the route (e.g., first, second, fastest, shortest).",
                                "examples": [["first", "fastest"]],
                            },
                        },
                    },
                    "description": "List of available route alternatives between the start and destination points.",
                }
            },
            "required": ["routes"],
            "additionalProperties": False,
        }
