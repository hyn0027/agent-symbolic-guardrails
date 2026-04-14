import json
from typing import Any, Dict, List, Optional

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


class NavigationAddOneWaypoint(Tool):
    """
    Navigation Control: Adds the specified waypoint between two existing adjacent
    waypoints in the current navigation route, using the provided connecting route segments.
    Only works if the navigation system is active. Returns the updated list of
    waypoints and route segments.
    """

    name = "navigation_add_one_waypoint"  # Tool name

    @staticmethod
    def invoke(
        waypoint_id_to_add: str,
        waypoint_id_before_new_waypoint: str,
        route_id_leading_to_new_waypoint: str,
        waypoint_id_after_new_waypoint: Optional[str] = None,
        route_id_leading_away_from_new_waypoint: Optional[str] = None,
    ) -> str:
        """
        Args:
            waypoint_id_to_add (str): The ID of the waypoint (location or POI) to insert.
            waypoint_id_before_new_waypoint (str): The ID of the waypoint immediately preceding the insertion point.
            waypoint_id_after_new_waypoint (str): The ID of the waypoint immediately following the insertion point.
            route_id_leading_to_new_waypoint (str): The ID of the route segment from 'waypoint_id_before_new_waypoint' to 'waypoint_id_to_add'.
            route_id_leading_away_from_new_waypoint (str): The ID of the route segment from 'waypoint_id_to_add' to 'waypoint_id_after_new_waypoint'.

        Returns:
            str: JSON string containing status, result (new waypoints/routes list), or errors.
        """
        response = {}
        vehicle_ctx = context_state.get()

        # --- Validate Input ID Formats ---
        if not check_correct_id_format(waypoint_id_to_add, "poi_or_location"):
            error_message = f"NavigationAddOneWaypoint_001: Invalid format for waypoint_id_to_add '{waypoint_id_to_add}'."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAV_ADD_WP_001": error_message}
            return json.dumps(response)
        if not check_correct_id_format(
            waypoint_id_before_new_waypoint, "poi_or_location"
        ):
            error_message = f"NavigationAddOneWaypoint_002: Invalid format for waypoint_id_before_new_waypoint '{waypoint_id_before_new_waypoint}'."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAV_ADD_WP_002": error_message}
            return json.dumps(response)
        if waypoint_id_after_new_waypoint is not None:
            if not check_correct_id_format(
                waypoint_id_after_new_waypoint, "poi_or_location"
            ):
                error_message = f"NavigationAddOneWaypoint_003: Invalid format for waypoint_id_after_new_waypoint '{waypoint_id_after_new_waypoint}'."
                tool_execution_errors_during_runtime.get().append(error_message)
                response["errors"] = {"NAV_ADD_WP_003": error_message}
                return json.dumps(response)
        if not check_correct_id_format(route_id_leading_to_new_waypoint, "route"):
            error_message = f"NavigationAddOneWaypoint_004: Invalid format for route_id_leading_to_new_waypoint '{route_id_leading_to_new_waypoint}'."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAV_ADD_WP_004": error_message}
            return json.dumps(response)
        if route_id_leading_away_from_new_waypoint is not None:
            if not check_correct_id_format(
                route_id_leading_away_from_new_waypoint, "route"
            ):
                error_message = f"NavigationAddOneWaypoint_005: Invalid format for route_id_leading_away_from_new_waypoint '{route_id_leading_away_from_new_waypoint}'."
                tool_execution_errors_during_runtime.get().append(error_message)
                response["errors"] = {"NAV_ADD_WP_005": error_message}
                return json.dumps(response)

        # --- Check Navigation State ---
        if not vehicle_ctx.navigation_active:
            error_message = "AUT-POL:017:: Navigation system is not active."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAV_ADD_WP_006": error_message}
            policy_errors_during_runtime.get().append(error_message)
            return json.dumps(response)

        # --- Validate Waypoint Existence and Order in Current Route ---
        current_waypoints = vehicle_ctx.waypoints_id or []
        try:
            idx_before = current_waypoints.index(waypoint_id_before_new_waypoint)
        except ValueError:
            error_message = f"NavigationAddOneWaypoint_007: Waypoint '{waypoint_id_before_new_waypoint}' not found in the current route's waypoints."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAV_ADD_WP_007": error_message}
            return json.dumps(response)

        # --- Validate Final Destination if no 'waypoint_id_after_new_waypoint' or 'route_id_leading_away_from_new_waypoint' is provided ---
        if (
            not waypoint_id_after_new_waypoint
            or not route_id_leading_away_from_new_waypoint
        ):
            if not idx_before == len(current_waypoints) - 1:
                # If the new waypoint is not the final destination, we need to provide the next waypoint and route leading away from it.
                error_message = f"NavigationAddOneWaypoint_008: New waypoint '{waypoint_id_to_add}' is not final destination, you have to provide waypoint_id_after_new_waypoint and  route_id_leading_away_from_new_waypoint."
                tool_execution_errors_during_runtime.get().append(error_message)
                response["errors"] = {"NAV_ADD_WP_008": error_message}
                return json.dumps(response)

        # Check if 'after' waypoint is immediately after 'before' waypoint
        if waypoint_id_after_new_waypoint:
            if (
                idx_before + 1 >= len(current_waypoints)
                or current_waypoints[idx_before + 1] != waypoint_id_after_new_waypoint
            ):
                error_message = f"NavigationAddOneWaypoint_009: Waypoint '{waypoint_id_after_new_waypoint}' does not immediately follow '{waypoint_id_before_new_waypoint}' in the current route."
                tool_execution_errors_during_runtime.get().append(error_message)
                response["errors"] = {"NAV_ADD_WP_009": error_message}
                return json.dumps(response)

        # --- Validate Provided Routes Using DataManager ---
        route_to_new = car_va_data_manager.get_route_by_id(
            route_id_leading_to_new_waypoint
        )
        if route_id_leading_away_from_new_waypoint:
            route_from_new = car_va_data_manager.get_route_by_id(
                route_id_leading_away_from_new_waypoint
            )

        if route_to_new is None:
            error_message = f"NavigationAddOneWaypoint_009: Route '{route_id_leading_to_new_waypoint}' (leading to new waypoint) not found."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAV_ADD_WP_009": error_message}
            return json.dumps(response)
        if route_id_leading_away_from_new_waypoint:
            if route_from_new is None:
                error_message = f"NavigationAddOneWaypoint_010: Route '{route_id_leading_away_from_new_waypoint}' (leading away from new waypoint) not found."
                tool_execution_errors_during_runtime.get().append(error_message)
                response["errors"] = {"NAV_ADD_WP_010": error_message}
                return json.dumps(response)

        # Check if route segments correctly connect the waypoints
        if route_to_new.get("start_id") != waypoint_id_before_new_waypoint:
            error_message = f"NavigationAddOneWaypoint_011: Route '{route_id_leading_to_new_waypoint}' does not start at '{waypoint_id_before_new_waypoint}'."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAV_ADD_WP_011": error_message}
            return json.dumps(response)
        if route_to_new.get("destination_id") != waypoint_id_to_add:
            error_message = f"NavigationAddOneWaypoint_012: Route '{route_id_leading_to_new_waypoint}' does not end at the new waypoint '{waypoint_id_to_add}'."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAV_ADD_WP_012": error_message}
            return json.dumps(response)
        if route_id_leading_away_from_new_waypoint:
            if route_from_new is not None:
                if route_from_new.get("start_id") != waypoint_id_to_add:
                    error_message = f"NavigationAddOneWaypoint_013: Route '{route_id_leading_away_from_new_waypoint}' does not start at the new waypoint '{waypoint_id_to_add}'."
                    tool_execution_errors_during_runtime.get().append(error_message)
                    response["errors"] = {"NAV_ADD_WP_013": error_message}
                    return json.dumps(response)
                if (
                    route_from_new.get("destination_id")
                    != waypoint_id_after_new_waypoint
                ):
                    error_message = f"NavigationAddOneWaypoint_014: Route '{route_id_leading_away_from_new_waypoint}' does not end at '{waypoint_id_after_new_waypoint}'."
                    tool_execution_errors_during_runtime.get().append(error_message)
                    response["errors"] = {"NAV_ADD_WP_014": error_message}
                    return json.dumps(response)
        # --- Update Context State ---
        # The index `idx_before` refers to the waypoint *before* the insertion point.
        # We need to insert the new waypoint *after* idx_before.
        # We need to replace the route segment at index `idx_before` with the two new routes.
        current_routes = vehicle_ctx.routes_to_final_destination_id or []

        if route_id_leading_away_from_new_waypoint and waypoint_id_after_new_waypoint:
            new_waypoints_list = (
                current_waypoints[: idx_before + 1]
                + [waypoint_id_to_add]
                + current_waypoints[idx_before + 1 :]
            )
            new_routes_list = (
                current_routes[:idx_before]
                + [
                    route_id_leading_to_new_waypoint,
                    route_id_leading_away_from_new_waypoint,
                ]
                + current_routes[idx_before + 1 :]
            )
        else:
            new_waypoints_list = current_waypoints[: idx_before + 1] + [
                waypoint_id_to_add
            ]
            new_routes_list = current_routes[:idx_before] + [
                route_id_leading_to_new_waypoint
            ]
        if safeguard_config.API_CHECK:  # AUT-POL:016
            if not check_waypoints_valid(new_waypoints_list):
                fixed_ctx = fixed_context.get()
                error_message = f"Violating policy AUT-POL:016: The start of the overall route set always has to be the current car location. The updated waypoints list after adding the new waypoint does not start with the current car location. The current car location is '{fixed_ctx.current_location.id}'"
                response["status"] = "REJECTED_BY_GUARDRAIL"
                response["errors"] = {"AUT-POL:016": error_message}
                policy_errors_during_runtime.get().append(error_message)
                return json.dumps(response)

        try:
            vehicle_ctx.update_state(
                waypoints_id=new_waypoints_list,
                routes_to_final_destination_id=new_routes_list,
            )
        except Exception as e:
            # Handle potential errors during state update
            # print(f"ERROR updating context state: {e}")
            error_message = (
                f"NavigationAddOneWaypoint_015: Failed to update navigation state: {e}."
            )
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAV_ADD_WP_015": error_message}
            return json.dumps(response)

        # --- Success ---
        response["status"] = "SUCCESS"
        response["result"] = {
            "waypoint_added": True,
            "new_waypoints_id": vehicle_ctx.waypoints_id,
            "new_routes_id": vehicle_ctx.routes_to_final_destination_id,
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
                "name": "navigation_add_one_waypoint",
                "description": "Navigation Control: adds the specified waypoint with the specified routes in the specified waypoint order. Only works if navigation system is active. Returns the navigation waypoint and routes with the waypoint and routes added.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": [
                        "waypoint_id_to_add",
                        "waypoint_id_before_new_waypoint",
                        "route_id_leading_to_new_waypoint",
                    ],
                    "properties": {
                        "waypoint_id_to_add": {
                            "type": "string",
                            "description": "The 'id' of the waypoint to add to the route.",
                        },
                        "waypoint_id_before_new_waypoint": {
                            "type": "string",
                            "description": "The 'id' of the waypoint before the new waypoint.",
                        },
                        "waypoint_id_after_new_waypoint": {
                            "type": "string",
                            "description": "The 'id' of the waypoint after the new waypoint. Mandatory if the new waypoint is not the final destination.",
                            "default": None,
                        },
                        "route_id_leading_to_new_waypoint": {
                            "type": "string",
                            "description": "The 'id' of the route leading to the new waypoint. Start has to match the 'waypoint_id_before_new_waypoint'.",
                        },
                        "route_id_leading_away_from_new_waypoint": {
                            "type": "string",
                            "description": "The 'id' of the route leading away from the new waypoint. Destination has to match the 'waypoint_id_after_new_waypoint'. Mandatory if the new waypoint is not the final destination.",
                            "default": None,
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
                "waypoint_added": {
                    "type": "boolean",
                    "description": "Indicates whether the new waypoint was successfully added to the navigation route. Always true if the operation succeeds.",
                    "examples": [True],
                },
                "new_waypoints_id": {
                    "type": "array",
                    "description": "List of waypoint IDs after the new waypoint was added. Includes the newly inserted waypoint at the correct position.",
                    "items": {
                        "type": "string",
                        "description": "ID of the waypoint.",
                    },
                    "examples": [["loc_ber_1001", "loc_poi_3920", "loc_dus_3007"]],
                },
                "new_routes_id": {
                    "type": "array",
                    "description": "List of route segment IDs after insertion. The route between the surrounding waypoints is replaced by two segments: to and from the new waypoint.",
                    "items": {
                        "type": "string",
                        "description": "ID of the route segment.",
                    },
                    "examples": [["rll_ber_poi_4001", "rll_poi_dus_3007"]],
                },
            },
            "required": ["waypoint_added", "new_waypoints_id", "new_routes_id"],
            "additionalProperties": False,
        }
