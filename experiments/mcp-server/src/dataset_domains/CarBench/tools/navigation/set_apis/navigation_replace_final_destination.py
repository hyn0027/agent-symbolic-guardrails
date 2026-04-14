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


class NavigationReplaceFinalDestination(Tool):
    "Navigation Control: replaces the final destination and the specified route leading to the new destination. Only works if navigation system is active. Returns the navigation waypoint and routes with the new destination set."

    @staticmethod
    def invoke(
        new_destination_id: str,
        route_id_leading_to_new_destination: str,
    ) -> str:
        """
        Args:
            new_destination_id (str): The 'id' of the new destination location or point of interest.
            route_id_leading_to_new_destination (str): Route ID from route that leads to the new destination. Start has to match the destination of the previous route (if there is any).
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): The new waypoints and routes with the new destination set.
            errors (dict): Error messages if the tool call was a "FAILURE".
        """
        response = {}
        vehicle_ctx = context_state.get()

        if check_correct_id_format(new_destination_id, "poi_or_location") == False:
            response["status"] = "FAILURE"
            error_message = (
                "NavigationReplaceFinalDestination_001: Invalid waypoint_id format."
            )
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_001": error_message}
            return json.dumps(response)
        if (
            check_correct_id_format(route_id_leading_to_new_destination, "route")
            == False
        ):
            response["status"] = "FAILURE"
            error_message = "NavigationReplaceFinalDestination_002: Invalid route_id_to_waypoint format."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_002": error_message}
            return json.dumps(response)

        if vehicle_ctx.navigation_active == False:
            response["status"] = "FAILURE"
            error_message = "AUT-POL:017: Navigation system is not active."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_003": error_message}
            policy_errors_during_runtime.get().append(error_message)
            return json.dumps(response)

        route_to_destination = car_va_data_manager.get_route_by_id(
            route_id_leading_to_new_destination
        )
        if route_to_destination is None:
            response["status"] = "FAILURE"
            error_message = "NavigationReplaceFinalDestination_004: Invalid route_id - route not found."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_005": error_message}
            return json.dumps(response)

        if route_to_destination["destination_id"] != new_destination_id:
            response["status"] = "FAILURE"
            error_message = "NavigationReplaceFinalDestination_005: Invalid route - destination of route leading to new destination does not match the destination."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_006": error_message}
            return json.dumps(response)

        if vehicle_ctx.waypoints_id[0] == new_destination_id:
            response["status"] = "FAILURE"
            error_message = "NavigationReplaceFinalDestination_006: Start cannot be replaced with this tool."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_008": error_message}
            return json.dumps(response)

        if route_to_destination["start_id"] != vehicle_ctx.waypoints_id[-2]:
            response["status"] = "FAILURE"
            error_message = "NavigationReplaceFinalDestination_007: Invalid route_id_to_waypoint - start of route does not match waypoint."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_REPLACE_ONE_WAYPOINT_010": error_message}
            return json.dumps(response)

        if safeguard_config.API_CHECK:  # AUT-POL:016
            if not check_waypoints_valid(
                vehicle_ctx.waypoints_id[:-1] + [new_destination_id]
            ):
                fixed_ctx = fixed_context.get()
                error_message = f"Violating policy AUT-POL:016: The start of the overall route set always has to be the current car location. The updated waypoints list after adding the new waypoint does not start with the current car location. The current car location is '{fixed_ctx.current_location.id}'"
                response["status"] = "REJECTED_BY_GUARDRAIL"
                response["errors"] = {"AUT-POL:016": error_message}
                policy_errors_during_runtime.get().append(error_message)
                return json.dumps(response)
        vehicle_ctx.update_state(
            waypoints_id=vehicle_ctx.waypoints_id[:-1] + [new_destination_id],
            routes_to_final_destination_id=vehicle_ctx.routes_to_final_destination_id[
                :-1
            ]
            + [route_id_leading_to_new_destination],
        )

        response["status"] = "SUCCESS"
        response["result"] = {
            "destination_replaced": True,
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
                "name": "navigation_replace_final_destination",
                "description": "Navigation Control: replaces the final destination and the specified route leading to the new destination. Only works if navigation system is active. Returns the navigation waypoint and routes with the new destination set.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": [
                        "new_destination_id",
                        "route_id_leading_to_new_destination",
                    ],
                    "properties": {
                        "new_destination_id": {
                            "type": "string",
                            "description": "The 'id' of the new destination location or point of interest.",
                        },
                        "route_id_leading_to_new_destination": {
                            "type": "string",
                            "description": "Route ID from route that leads to the new destination. Start has to match the destination of the previous route (if there is any).",
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
                "destination_replaced": {
                    "type": "boolean",
                    "description": "Indicates whether the final destination was successfully replaced. Always true if the operation succeeds.",
                    "examples": [True],
                },
                "new_waypoints": {
                    "type": "array",
                    "description": "List of waypoint IDs after replacing the final destination. The previous final destination is replaced with the new destination ID.",
                    "items": {"type": "string", "description": "ID of the waypoint."},
                    "examples": [["loc_muc_001", "loc_stu_002", "loc_ham_003"]],
                },
                "new_routes": {
                    "type": "array",
                    "description": "List of route segment IDs after replacing the final destination. The last route segment is replaced with the provided route leading to the new destination.",
                    "items": {
                        "type": "string",
                        "description": "ID of the route segment.",
                    },
                    "examples": [["rll_muc_stu_9001", "rll_stu_ham_9002"]],
                },
            },
            "required": ["destination_replaced", "new_waypoints", "new_routes"],
            "additionalProperties": False,
        }
