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


class NavigationDeleteOneWaypoint(Tool):
    "Navigation Control: deletes the specified waypoint from the route set. Additionaly the route replacing the routes via the waypoint has the provided and will be set. Only works if navigation system is active and a multi-stop route is set. Returns the navigation waypoint and routes with the waypoints deleted."

    @staticmethod
    def invoke(waypoint_id_to_delete: str, route_id_without_waypoint: str) -> str:
        """
        Args:
            waypoint_id_to_delete (str): The 'id' of the waypoint to delete.
            route_id_without_waypoint (str): The 'id' of the route that should be set without the waypoint instead of the routes via the waypoint. Start has the match the previous waypoint of the deleted waypoint and destination has to match the next waypoint of the deleted waypoint.
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): The new waypoints and routes with the waypoint deleted and the alternative route set.
            errors (dict): Error messages if the tool call was a "FAILURE".
        """
        response = {}
        vehicle_ctx = context_state.get()

        if check_correct_id_format(waypoint_id_to_delete, "poi_or_location") == False:
            response["status"] = "FAILURE"
            error_message = (
                "NavigationDeleteOneWaypoint_001: Invalid waypoint_id format."
            )
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_DELETE_WAYPOINT_001": error_message}
            return json.dumps(response)
        if check_correct_id_format(route_id_without_waypoint, "route") == False:
            response["status"] = "FAILURE"
            error_message = "NavigationDeleteOneWaypoint_002: Invalid route_id_without_waypoint format."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_DELETE_WAYPOINT_002": error_message}
            return json.dumps(response)

        if vehicle_ctx.navigation_active == False:
            response["status"] = "FAILURE"
            error_message = "AUT-POL:017: Navigation system is not active."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_DELETE_WAYPOINT_003": error_message}
            policy_errors_during_runtime.get().append(error_message)
            return json.dumps(response)

        route_without_waypoint = car_va_data_manager.get_route_by_id(
            route_id_without_waypoint
        )
        if route_without_waypoint is None:
            response["status"] = "FAILURE"
            error_message = (
                "NavigationDeleteOneWaypoint_004: Invalid route_id - route not found."
            )
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_DELETE_WAYPOINT_004": error_message}
            return json.dumps(response)

        try:
            # find index of waypoint_id in waypoints_id
            waypoint_idx_to_delete = vehicle_ctx.waypoints_id.index(
                waypoint_id_to_delete
            )
        except Exception as e:
            response["status"] = "FAILURE"
            error_message = "NavigationDeleteOneWaypoint_005: Invalid waypoint_id to delete - waypoint not found."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_DELETE_WAYPOINT_005": error_message}
            return json.dumps(response)

        if (
            route_without_waypoint["destination_id"]
            != vehicle_ctx.waypoints_id[waypoint_idx_to_delete + 1]
        ):
            response["status"] = "FAILURE"
            error_message = "NavigationDeleteOneWaypoint_006: Invalid route - destination of route does not match the next waypoint of the to delete waypoint."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_DELETE_WAYPOINT_006": error_message}
            return json.dumps(response)

        if (
            route_without_waypoint["start_id"]
            != vehicle_ctx.waypoints_id[waypoint_idx_to_delete - 1]
        ):
            response["status"] = "FAILURE"
            error_message = "NavigationDeleteOneWaypoint_007: Invalid route - start of route does not match the previous waypoint of the to delete waypoint."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_DELETE_WAYPOINT_007": error_message}
            return json.dumps(response)

        if (
            vehicle_ctx.waypoints_id[-1] == waypoint_id_to_delete
            or vehicle_ctx.waypoints_id[0] == waypoint_id_to_delete
        ):
            response["status"] = "FAILURE"
            error_message = "NavigationDeleteOneWaypoint_008: Start or final destination cannot be deleted with this tool."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_DELETE_WAYPOINT_008": error_message}
            return json.dumps(response)

        new_waypoints = (
            vehicle_ctx.waypoints_id[:waypoint_idx_to_delete]
            + vehicle_ctx.waypoints_id[waypoint_idx_to_delete + 1 :]
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
            waypoints_id=vehicle_ctx.waypoints_id[:waypoint_idx_to_delete]
            + vehicle_ctx.waypoints_id[waypoint_idx_to_delete + 1 :],
            routes_to_final_destination_id=vehicle_ctx.routes_to_final_destination_id[
                : waypoint_idx_to_delete - 1
            ]
            + [route_id_without_waypoint]
            + vehicle_ctx.routes_to_final_destination_id[waypoint_idx_to_delete + 1 :],
        )

        response["status"] = "SUCCESS"
        response["result"] = {
            "waypoint_deleted": True,
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
                "name": "navigation_delete_waypoint",
                "description": "Navigation Control: deletes the specified waypoint from the route set. Additionaly the route replacing the routes via the waypoint has the provided and will be set. Only works if navigation system is active and a multi-stop route is set. Returns the navigation waypoint and routes with the waypoint deleted and the replacing route set.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["waypoint_id_to_delete", "route_id_without_waypoint"],
                    "properties": {
                        "waypoint_id_to_delete": {
                            "type": "string",
                            "description": "The 'id' of the waypoint to delete.",
                        },
                        "route_id_without_waypoint": {
                            "type": "string",
                            "description": "The 'id' of the route that should be set without the waypoint instead of the routes via the waypoint. Start has the match the previous waypoint of the deleted waypoint and destination has to match the next waypoint of the deleted waypoint.",
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
                "waypoint_deleted": {
                    "type": "boolean",
                    "description": "Indicates whether the waypoint was successfully deleted from the navigation route. Always true if the operation succeeds.",
                    "examples": [True],
                },
                "new_waypoints": {
                    "type": "array",
                    "description": "List of waypoint IDs after the specified waypoint was deleted. The deleted waypoint is removed from the list.",
                    "items": {"type": "string", "description": "ID of the waypoint."},
                    "examples": [["loc_ber_1001", "loc_poi_3920", "loc_dus_3007"]],
                },
                "new_routes": {
                    "type": "array",
                    "description": "List of route segment IDs after the specified waypoint was deleted. The two route segments around the deleted waypoint are replaced by the single provided route.",
                    "items": {
                        "type": "string",
                        "description": "ID of the route segment.",
                    },
                    "examples": [["rll_ber_poi_4001", "rll_poi_dus_3007"]],
                },
            },
            "required": ["waypoint_deleted", "new_waypoints", "new_routes"],
            "additionalProperties": False,
        }
