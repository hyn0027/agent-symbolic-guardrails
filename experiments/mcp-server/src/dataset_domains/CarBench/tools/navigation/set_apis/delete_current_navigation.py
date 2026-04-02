import json
from typing import Any, Dict, List, Union

from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.tools.helper_functions import (
    check_correct_id_format,
)
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class DeleteCurrentNavigation(Tool):
    "Navigation Control: deletes the currently set navigation. Turns the navigation system to inactive and deletes all waypoints and routes."

    @staticmethod
    def invoke() -> str:
        """
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): The new navigation state.
            errors (dict): Error messages if the tool call was a "FAILURE".
        """
        response = {}
        vehicle_ctx = context_state.get()

        vehicle_ctx.update_state(
            navigation_active=False,
            waypoints_id=[],
            routes_to_final_destination_id=[],
        )

        response["status"] = "SUCCESS"
        response["result"] = {
            "navigation_active": vehicle_ctx.navigation_active,
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
                "name": "delete_current_navigation",
                "description": "Navigation Control: deletes the currently set navigation. Turns the navigation system to inactive and deletes all waypoints and routes.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {},
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
                    "description": "Indicates whether navigation is currently active. After deletion, this is always set to false.",
                    "examples": [False],
                },
                "new_waypoints": {
                    "type": "array",
                    "description": "List of waypoint IDs after deletion. This will be an empty list after successful navigation deletion.",
                    "items": {
                        "type": "string",
                        "description": "ID of the waypoint.",
                    },
                    "examples": [["loc_mun_2389"]],
                },
                "new_routes": {
                    "type": "array",
                    "description": "List of route segment IDs to the final destination after deletion. This will be an empty list after successful navigation deletion.",
                    "items": {
                        "type": "string",
                        "description": "ID of the route segment.",
                    },
                    "examples": [["rll_mun_ham_1001"]],
                },
            },
            "required": ["navigation_active", "new_waypoints", "new_routes"],
            "additionalProperties": False,
        }
