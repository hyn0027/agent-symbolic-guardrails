import json
from typing import Any, Dict, List, Union

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
    check_waypoints_valid,
)
from dataset_domains.CarBench.context.fixed_context import (
    fixed_context,
)
from dataset_domains.CarBench.mock_data import car_va_data_manager
from dataset_domains.CarBench.tools.helper_functions import (
    check_correct_id_format,
)
from dataset_domains.CarBench.policy_evaluator import policy_errors_during_runtime
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)

from config_loader import CONFIG

safeguard_config = CONFIG.SAFEGUARD


class NavigationReplaceOneWaypoint(Tool):
    "Navigation Control: replaces one waypoint. Only works if navigation system is active and a multi-stop route is set."

    @staticmethod
    def invoke(
        waypoint_id_to_replace: str,
        new_waypoint_id: str,
        route_id_leading_to_new_waypoint: str,
        route_id_leading_away_from_new_waypoint: str,
    ) -> str:
        """
        Args:
            waypoint_id_to_replace (str): The 'id' of the waypoint to replace.
            new_waypoint_id (str): The 'id' of the new waypoint location or point of interest.
            route_id_leading_to_new_waypoint (str): Route ID from route that leads to the new waypoint. Start has to match the destination of the previous route (if there is any).
            route_id_leading_away_from_new_waypoint (str): Route ID from the route that leads away from the new waypoint. Destination has to match the start of the next route (if there is any).
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): The new waypoints and routes with the new waypoint set.
            errors (dict): Error messages if the tool call was a "FAILURE".
        """
        response = {}
        vehicle_ctx = context_state.get()

        if check_correct_id_format(waypoint_id_to_replace, "poi_or_location") == False:
            response["status"] = "FAILURE"
            error_message = (
                "NavigationReplaceOneWaypoint_001: Invalid waypoint_id format."
            )
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_001": error_message}
            return json.dumps(response)
        if check_correct_id_format(new_waypoint_id, "poi_or_location") == False:
            response["status"] = "FAILURE"
            error_message = (
                "NavigationReplaceOneWaypoint_002: Invalid new_waypoint_id format."
            )
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_002": error_message}
            return json.dumps(response)
        if check_correct_id_format(route_id_leading_to_new_waypoint, "route") == False:
            response["status"] = "FAILURE"
            error_message = (
                "NavigationReplaceOneWaypoint_003: Invalid route_id_to_waypoint format."
            )
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_003": error_message}
            return json.dumps(response)
        if (
            check_correct_id_format(route_id_leading_away_from_new_waypoint, "route")
            == False
        ):
            response["status"] = "FAILURE"
            error_message = "NavigationReplaceOneWaypoint_004: Invalid route_id_from_waypoint format."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_004": error_message}
            return json.dumps(response)

        if vehicle_ctx.navigation_active == False:
            response["status"] = "FAILURE"
            error_message = "AUT-POL:017: Navigation system is not active."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_005": error_message}
            policy_errors_during_runtime.get().append(error_message)
            return json.dumps(response)

        route_to_waypoint = car_va_data_manager.get_route_by_id(
            route_id_leading_to_new_waypoint
        )
        route_from_waypoint = car_va_data_manager.get_route_by_id(
            route_id_leading_away_from_new_waypoint
        )
        if route_to_waypoint is None:
            response["status"] = "FAILURE"
            error_message = "NavigationReplaceOneWaypoint_006: Invalid route_id to waypoint - route not found."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_006": error_message}
            return json.dumps(response)

        if route_from_waypoint is None:
            response["status"] = "FAILURE"
            error_message = "NavigationReplaceOneWaypoint_007: Invalid route_id from waypoint - route not found."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_007": error_message}
            return json.dumps(response)

        if route_to_waypoint["destination_id"] != new_waypoint_id:
            response["status"] = "FAILURE"
            error_message = "NavigationReplaceOneWaypoint_008: Invalid route - destination of route leading to new waypoint does not match the new waypoint."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_008": error_message}
            return json.dumps(response)

        if route_from_waypoint["start_id"] != new_waypoint_id:
            response["status"] = "FAILURE"
            error_message = "NavigationReplaceOneWaypoint_009: Invalid route - start of route leading away from new waypoint does not match the new waypoint."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_009": error_message}
            return json.dumps(response)

        if (
            vehicle_ctx.waypoints_id[-1] == new_waypoint_id
            or vehicle_ctx.waypoints_id[0] == new_waypoint_id
        ):
            response["status"] = "FAILURE"
            error_message = "NavigationReplaceOneWaypoint_010: Start or final destination cannot be replaced with this tool."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_010": error_message}
            return json.dumps(response)

        try:
            # find index of waypoint_id in waypoints_id
            waypoint_idx_to_replace = vehicle_ctx.waypoints_id.index(
                waypoint_id_to_replace
            )
        except Exception as e:
            response["status"] = "FAILURE"
            error_message = "NavigationReplaceOneWaypoint_011: Invalid waypoint_id to replace - waypoint not found."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_011": error_message}
            return json.dumps(response)

        if (
            route_to_waypoint["start_id"]
            != vehicle_ctx.waypoints_id[waypoint_idx_to_replace - 1]
        ):
            response["status"] = "FAILURE"
            error_message = "NavigationReplaceOneWaypoint_012: Invalid route_id_to_waypoint - start of route does not match previous waypoint."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_012": error_message}
            return json.dumps(response)
        if (
            route_from_waypoint["destination_id"]
            != vehicle_ctx.waypoints_id[waypoint_idx_to_replace + 1]
        ):
            response["status"] = "FAILURE"
            error_message = "NavigationReplaceOneWaypoint_013: Invalid route_id_from_waypoint - destination of route does not match next waypoint."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_013": error_message}
            return json.dumps(response)

        new_waypoints = (
            vehicle_ctx.waypoints_id[:waypoint_idx_to_replace]
            + [new_waypoint_id]
            + vehicle_ctx.waypoints_id[waypoint_idx_to_replace + 1 :]
        )
        if safeguard_config.API_CHECK:  # AUT-POL:016
            if not check_waypoints_valid(new_waypoints):
                fixed_ctx = fixed_context.get()
                error_message = f"Violating policy AUT-POL:016: The start of the overall route set always has to be the current car location. The updated waypoints list after adding the new waypoint does not start with the current car location. The current car location is '{fixed_ctx.current_location.id}'"
                response["status"] = "REJECTED_BY_GUARDRAIL"
                response["errors"] = {"AUT-POL:016": error_message}
                policy_errors_during_runtime.get().append(error_message)
                return json.dumps(response)
        vehicle_ctx.update_state(
            waypoints_id=vehicle_ctx.waypoints_id[:waypoint_idx_to_replace]
            + [new_waypoint_id]
            + vehicle_ctx.waypoints_id[waypoint_idx_to_replace + 1 :],
            routes_to_final_destination_id=vehicle_ctx.routes_to_final_destination_id[
                : waypoint_idx_to_replace - 1
            ]
            + [route_id_leading_to_new_waypoint]
            + [route_id_leading_away_from_new_waypoint]
            + vehicle_ctx.routes_to_final_destination_id[waypoint_idx_to_replace + 1 :],
        )

        response["status"] = "SUCCESS"
        response["result"] = {
            "waypoint_replaced": True,
            "new_waypoints": vehicle_ctx.waypoints_id,
            "new_routes": vehicle_ctx.routes_to_final_destination_id,
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
                "name": "navigation_replace_one_waypoint",
                "description": "Navigation Control: replaces one waypoint and the specified routes leading to the new waypoint and away from the new waypoint. Only works if navigation system is active and a multi-stop route is set. Returns the navigation waypoint and routes with the new waypoints set.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": [
                        "waypoint_id_to_replace",
                        "new_waypoint_id",
                        "route_id_leading_to_new_waypoint",
                        "route_id_leading_away_from_new_waypoint",
                    ],
                    "properties": {
                        "waypoint_id_to_replace": {
                            "type": "string",
                            "description": "The 'id' of the waypoint to replace.",
                        },
                        "new_waypoint_id": {
                            "type": "string",
                            "description": "The 'id' of the waypoint to include in the new route.",
                        },
                        "route_id_leading_to_new_waypoint": {
                            "type": "string",
                            "description": "Route ID from route that leads to the new waypoint, destination of the route is the new waypoint. Start has to match the destination of the previous route (if there is any).",
                        },
                        "route_id_leading_away_from_new_waypoint": {
                            "type": "string",
                            "description": "Route ID from the route that leads away from the new waypoint, start of the route is the new waypoint. Destination has to match the start of the next route (if there is any).",
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
                "waypoint_replaced": {
                    "type": "boolean",
                    "description": "Indicates whether the waypoint was successfully replaced.",
                    "examples": [True],
                },
                "new_waypoints": {
                    "type": "array",
                    "description": "Updated list of waypoint IDs after replacing the specified waypoint.",
                    "items": {"type": "string", "description": "ID of the waypoint."},
                    "examples": [["loc_muc_001", "loc_nue_002", "loc_ham_003"]],
                },
                "new_routes": {
                    "type": "array",
                    "description": "Updated list of route IDs after replacing the waypoint, including new routes to and from the new waypoint.",
                    "items": {
                        "type": "string",
                        "description": "ID of the route segment.",
                    },
                    "examples": [["rll_muc_nue_101", "rll_nue_ham_102"]],
                },
            },
            "required": ["waypoint_replaced", "new_waypoints", "new_routes"],
            "additionalProperties": False,
        }
