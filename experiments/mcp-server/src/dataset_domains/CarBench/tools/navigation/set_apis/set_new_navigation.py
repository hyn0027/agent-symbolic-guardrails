import json
from typing import Any, Dict, List, Union

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)

# from tau_bench.envs.car_voice_assistant.data import get_route_by_id
from dataset_domains.CarBench.mock_data import car_va_data_manager
from dataset_domains.CarBench.tools.helper_functions import (
    check_correct_id_format,
)
from dataset_domains.CarBench.policy_evaluator import policy_errors_during_runtime
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class SetNewNavigation(Tool):
    "Navigation Control: sets and starts new navigation in the navigation system. It fully replaces any previously set navigation. If multiple route 'id' are given it automatically sets a waypoint."

    @staticmethod
    def invoke(route_ids: List[str]) -> str:
        """
        Args:
            route_ids (list): Ordered list of route IDs to set for navigation. Order of list is from start, over optional waypoints, to destination. If multiple route 'id' are given, the destination of the first route has to match the start of next route.
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Points of interest information for the specified location and category.
            errors (dict): Error messages if the tool call was a "FAILURE".
        """
        response = {}
        vehicle_ctx = context_state.get()

        number_of_routes = len(route_ids)
        selected_routes = []
        waypoint_ids = []

        if vehicle_ctx.navigation_active == True:
            response["status"] = "FAILURE"
            error_message = "SetNewNavigation_001: Navigation already active. Use editing tools or delete current navigation first."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SET_NAVIGATION_001": error_message}
            policy_errors_during_runtime.get().append(
                f"SetNewNavigation_001: {error_message}"
            )
            return json.dumps(response)
        for idx, route in enumerate(route_ids):
            if check_correct_id_format(route, "route") == False:
                response["status"] = "FAILURE"
                error_message = (
                    f"SetNewNavigation_002: Invalid route_id format for route {route}."
                )
                tool_execution_errors_during_runtime.get().append(error_message)
                response["errors"] = {"SET_NAVIGATION_002": error_message}
                return json.dumps(response)

            # get current route + next route if available to check if destination of current route is the start of the next route
            if idx == 0:
                selected_route = car_va_data_manager.get_route_by_id(route)
                waypoint_ids.append(selected_route["start_id"])
                if selected_route == None:
                    response["status"] = "FAILURE"
                    error_message = f"SetNewNavigation_003: Invalid route_id - route {route} not found."
                    tool_execution_errors_during_runtime.get().append(error_message)
                    response["errors"] = {"SET_NAVIGATION_003": error_message}
                    return json.dumps(response)
            else:
                selected_route = next_route
            if idx < number_of_routes - 1:
                next_route = car_va_data_manager.get_route_by_id(route_ids[idx + 1])
                if next_route == None:
                    response["status"] = "FAILURE"
                    error_message = f"SetNewNavigation_004: Invalid route_id - route {route} not found."
                    tool_execution_errors_during_runtime.get().append(error_message)
                    response["errors"] = {"SET_NAVIGATION_004": error_message}
                    return json.dumps(response)
                if selected_route["destination_id"] != next_route["start_id"]:
                    response["status"] = "FAILURE"
                    error_message = f"SetNewNavigation_005: Invalid routes. Destination of route at index {idx} does not match the start of the route at index {idx+1}."
                    tool_execution_errors_during_runtime.get().append(error_message)
                    response["errors"] = {"SET_NAVIGATION_005": error_message}
                    return json.dumps(response)
            selected_routes.append(selected_route)
            waypoint_ids.append(selected_route["destination_id"])

        vehicle_ctx.update_state(
            navigation_active=True,
            waypoints_id=waypoint_ids,
            routes_to_final_destination_id=route_ids,
        )

        response["status"] = "SUCCESS"
        response["result"] = {
            "navigation_set": True,
            "start_id": selected_routes[0]["start_id"],
            "waypoints": waypoint_ids,
            "destination_id": waypoint_ids[-1],
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
                "name": "set_new_navigation",
                "description": "Navigation Control: sets and starts new navigation in the navigation system. It fully replaces any previously set navigation. If multiple route 'id' are given it automatically sets a waypoint. It activates the navigation system and returns the waypoints set.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["route_ids"],
                    "properties": {
                        "route_ids": {
                            "type": "array",
                            "description": "Ordered list of route IDs to set for navigation. Order of list is from start, over optional waypoints, to destination. If multiple route 'id' are given, the destination of the first route has to match the start of next route.",
                            "items": {
                                "type": "string",
                                "description": "The route 'id' of the corresponding route part.",
                            },
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
                "navigation_set": {
                    "type": "boolean",
                    "description": "Indicates whether the navigation was successfully set and activated.",
                    "examples": [True],
                },
                "start_id": {
                    "type": "string",
                    "description": "The ID of the starting point of the navigation route.",
                    "examples": ["loc_muc_001"],
                },
                "waypoints": {
                    "type": "array",
                    "description": "Ordered list of location or POI IDs from start to destination, including optional waypoints.",
                    "items": {
                        "type": "string",
                        "description": "Location or POI ID used as waypoint.",
                    },
                    "examples": [["loc_muc_001", "loc_nue_002", "loc_ham_003"]],
                },
                "destination_id": {
                    "type": "string",
                    "description": "The ID of the final destination in the navigation route.",
                    "examples": ["loc_ham_003"],
                },
            },
            "required": ["navigation_set", "start_id", "waypoints", "destination_id"],
            "additionalProperties": False,
        }
