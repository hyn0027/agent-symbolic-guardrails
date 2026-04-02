import json
from typing import Any, Dict, List, Optional, Union  # Added List, Optional

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.mock_data import car_va_data_manager
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class GetCurrentNavigationState(Tool):
    """
    Navigation State Information: Gets the current navigation state, including
    active status, list of waypoint IDs, and list of route segment IDs forming
    the current trip. Optionally retrieves detailed information for these waypoints
    and routes.
    """

    name = "get_current_navigation_state"

    @staticmethod
    def invoke(detailed_information: bool = False) -> str:
        """
        Args:
            detailed_information (bool): If False (default), only waypoint and route IDs are returned.
                                         If True, details (name, position, route specifics) are also fetched.
        Returns:
            str: JSON string containing status, result (navigation state info), or errors.
        """
        response = {}
        vehicle_ctx = context_state.get()  # Get the current navigation context

        # Basic state information always included
        basic_state = {
            "navigation_active": vehicle_ctx.navigation_active,
            "waypoints_id": vehicle_ctx.waypoints_id
            or [],  # Ensure lists exist even if empty
            "routes_to_final_destination_id": vehicle_ctx.routes_to_final_destination_id
            or [],
        }

        # --- Handle simple request (IDs only) ---
        if not detailed_information:
            response["status"] = "SUCCESS"
            response["result"] = basic_state
            return json.dumps(response)

        # --- Handle detailed request ---
        # Check if DataManager is available, needed for details
        if car_va_data_manager is None:
            response["status"] = "FAILURE"
            error_message = "GetCurrentNavigationState_001: Core Data Manager failed to initialize (needed for detailed info)."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_CURRENT_NAVIGATION_STATE_001": error_message}
            return json.dumps(response)

        waypoint_details: List[Optional[Dict[str, Any]]] = []
        route_details: List[Optional[Dict[str, Any]]] = []
        fetch_errors: List[str] = (
            []
        )  # Collect errors encountered during detail fetching

        # Fetch Waypoint Details
        for waypoint_id in basic_state["waypoints_id"]:
            detail = None
            if waypoint_id.startswith("loc_"):
                detail = car_va_data_manager.get_location_by_id(waypoint_id)
            elif waypoint_id.startswith("poi_"):
                detail = car_va_data_manager.get_poi_by_id(waypoint_id)
            else:
                fetch_errors.append(
                    f"Waypoint '{waypoint_id}' has an unrecognized format."
                )
                detail = {
                    "id": waypoint_id,
                    "error": "Unrecognized format",
                }  # Add placeholder with error

            if (
                detail is None
                and not waypoint_id.startswith("loc_")
                and not waypoint_id.startswith("poi_")
            ):
                # Only add error if it wasn't added above due to format
                fetch_errors.append(
                    f"Details for waypoint '{waypoint_id}' could not be found."
                )
                detail = {
                    "id": waypoint_id,
                    "error": "Not found",
                }  # Add placeholder with error

            # We append None or the placeholder if not found to maintain list order correspondence
            waypoint_details.append(detail)

        # Fetch Route Details
        for route_id in basic_state["routes_to_final_destination_id"]:
            detail = car_va_data_manager.get_route_by_id(route_id)
            if detail is None:
                fetch_errors.append(
                    f"Details for route '{route_id}' could not be found."
                )
                detail = {
                    "id": route_id,
                    "error": "Not found",
                }  # Add placeholder with error
            route_details.append(detail)

        # --- Format Detailed Response ---
        response["status"] = "SUCCESS"  # Still success, but might include fetch errors
        response["result"] = {
            **basic_state,  # Include the basic IDs
            "details": {"waypoints": waypoint_details, "routes": route_details},
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
                "name": "get_current_navigation_state",
                "description": "Navigation State Information: gets the navigation state including if the navigation is active and the currently selected route. The route information includes the current waypoint 'id's and the current selected route part 'id's. If parameter 'detailed_information' is set, additional information about the waypoint names, positions, and the route starts, destinations, distances, and durations is returned.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": [],
                    "properties": {
                        "detailed_information": {
                            "type": "boolean",
                            "description": "If False, only waypoint and route 'id's are returned. If True, additional information about the waypoint names, positions; and the route starts, destinations, distances, durations is returned.",
                            "default": False,
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
                "navigation_active": {
                    "type": "boolean",
                    "description": "Indicates if the navigation is currently active.",
                    "examples": [True],
                },
                "waypoints_id": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of waypoint IDs for the current trip.",
                    "examples": [["loc_mun_9995", "loc_erf_4101", "loc_ham_6805"]],
                },
                "routes_to_final_destination_id": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of route segment IDs leading to the final destination.",
                    "examples": [["rll_mun_erf_9149", "rll_erf_ham_4348"]],
                },
                "details": {
                    "type": "object",
                    "description": "Detailed information about waypoints and routes. Output present if detailed_information was set to True.",
                    "properties": {
                        "waypoints": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "description": "The ID of the waypoint. Present if detailed_information was set to True.",
                                        "examples": ["loc_mun_9995"],
                                    },
                                    "name": {
                                        "type": "string",
                                        "description": "The name of the waypoint. Present if detailed_information was set to True.",
                                        "examples": ["Munich"],
                                    },
                                    "position": {
                                        "type": "object",
                                        "description": "The geographical position of the waypoint. Present if detailed_information was set to True.",
                                        "properties": {
                                            "latitude": {
                                                "type": "number",
                                                "description": "Latitude of the waypoint.",
                                                "examples": [48.1375],
                                            },
                                            "longitude": {
                                                "type": "number",
                                                "description": "Longitude of the waypoint.",
                                                "examples": [11.575],
                                            },
                                        },
                                    },
                                },
                            },
                            "description": "List of detailed waypoint information. Present if detailed_information was set to True.",
                        },
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
                                        "description": " ID of Starting point of the route. Present if detailed_information was set to True.",
                                        "examples": ["loc_mun_9995"],
                                    },
                                    "destination_id": {
                                        "type": "string",
                                        "description": "Destination of the route. Present if detailed_information was set to True.",
                                        "examples": ["loc_erf_4101"],
                                    },
                                    "name_via": {
                                        "type": "string",
                                        "description": "Name of the route via streets. Present if detailed_information was set to True.",
                                        "examples": ["K152, K277, K88"],
                                    },
                                    "distance_km": {
                                        "type": "number",
                                        "description": "Distance of the route in kilometers. Present if detailed_information was set to True.",
                                        "examples": [15.5],
                                    },
                                    "duration_hours": {
                                        "type": "number",
                                        "description": "Estimated duration of the route, hour information. Present if detailed_information was set to True.",
                                        "examples": [3],
                                    },
                                    "duration_minutes": {
                                        "type": "number",
                                        "description": "Estimated duration of the route, minute information. Present if detailed_information was set to True.",
                                        "examples": [30],
                                    },
                                    "road_types": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Types of roads included in the route (e.g., highway, urban, country roads). Present if detailed_information was set to True.",
                                        "examples": [["highway", "urban"]],
                                    },
                                    "includes_toll": {
                                        "type": "boolean",
                                        "description": "Indicates if the route includes toll roads. Present if detailed_information was set to True.",
                                        "examples": [True],
                                    },
                                    "alias": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Aliases for the route (e.g., first/second, fastest, shortest). Present if detailed_information was set to True.",
                                        "examples": [["first", "fastest"]],
                                    },
                                },
                            },
                            "description": "List of detailed route information. Present if detailed_information was set to True.",
                        },
                    },
                },
            },
            "required": [
                "navigation_active",
                "waypoints_id",
                "routes_to_final_destination_id",
            ],
            "additionalProperties": False,
        }
