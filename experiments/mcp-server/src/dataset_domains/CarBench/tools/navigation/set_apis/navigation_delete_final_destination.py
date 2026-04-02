import json
from typing import Any, Dict, List, Union

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.helper_functions import (
    check_correct_id_format,
)
from dataset_domains.CarBench.policy_evaluator import policy_errors_during_runtime
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class NavigationDeleteFinalDestination(Tool):
    "Navigation Control: deletes the destination from the route set, with this the last intermediate stop becomes the new destination. Only works if navigation system is active and a multi-stop route is set. Returns the navigation waypoint and routes with the destination and corresponding route deleted."

    @staticmethod
    def invoke(destination_id_to_delete: str) -> str:
        """
        Args:
            destination_id_to_delete (str): The 'id' of the destination to delete
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): The new waypoints and routes with the destination deleted.
            errors (dict): Error messages if the tool call was a "FAILURE".
        """
        response = {}
        vehicle_ctx = context_state.get()

        if (
            check_correct_id_format(destination_id_to_delete, "poi_or_location")
            == False
        ):
            response["status"] = "FAILURE"
            error_message = (
                "NavigationDeleteFinalDestination_001: Invalid waypoint_id format."
            )
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_DELETE_DESTINATION_001": error_message}
            return json.dumps(response)

        if vehicle_ctx.navigation_active == False:
            response["status"] = "FAILURE"
            error_message = "AUT-POL:017: Navigation system is not active."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_DELETE_DESTINATION_002": error_message}
            policy_errors_during_runtime.get().append(error_message)
            return json.dumps(response)

        if len(vehicle_ctx.waypoints_id) < 3:
            response["status"] = "FAILURE"
            error_message = "AUT-POL:019: No intermediate waypoints, destination deletion would lead to full deletion of navigation."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_DELETE_DESTINATION_003": error_message}
            policy_errors_during_runtime.get().append(error_message)
            return json.dumps(response)

        if vehicle_ctx.waypoints_id[-1] != destination_id_to_delete:
            response["status"] = "FAILURE"
            error_message = "NavigationDeleteFinalDestination_004: Invalid destination_id_to_delete - does not match currently set destination."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"NAVIGATION_DELETE_DESTINATION_004": error_message}
            return json.dumps(response)

        vehicle_ctx.update_state(
            waypoints_id=vehicle_ctx.waypoints_id[:-1],
            routes_to_final_destination_id=vehicle_ctx.routes_to_final_destination_id[
                :-1
            ],
        )

        response["status"] = "SUCCESS"
        response["result"] = {
            "destination_deleted": True,
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
                "name": "navigation_delete_destination",
                "description": "Navigation Control: deletes the destination from the route set, with this the last intermediate stop becomes the new destination. Only works if navigation system is active and a multi-stop route is set. Returns the navigation waypoint and routes with the destination and corresponding route deleted.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["destination_id_to_delete"],
                    "properties": {
                        "destination_id_to_delete": {
                            "type": "string",
                            "description": "The 'id' of the destination to delete.",
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
                "destination_deleted": {
                    "type": "boolean",
                    "description": "Indicates whether the destination was successfully deleted from the navigation route. Always true if the operation succeeds.",
                    "examples": [True],
                },
                "new_waypoints": {
                    "type": "array",
                    "description": "List of waypoint IDs after the destination was deleted. The last intermediate stop becomes the new destination.",
                    "items": {"type": "string", "description": "ID of the waypoint."},
                    "examples": [["loc_ber_1001", "loc_poi_3920"]],
                },
                "new_routes": {
                    "type": "array",
                    "description": "List of route segment IDs after the destination was deleted. The segment leading to the deleted destination is removed.",
                    "items": {
                        "type": "string",
                        "description": "ID of the route segment.",
                    },
                    "examples": [["rll_ber_poi_4001"]],
                },
            },
            "required": ["destination_deleted", "new_waypoints", "new_routes"],
            "additionalProperties": False,
        }
