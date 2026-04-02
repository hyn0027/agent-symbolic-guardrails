import json
from typing import Any, Dict, Optional, Union

from dataset_domains.CarBench.mock_data import car_va_data_manager
from dataset_domains.CarBench.tools.helper_functions import (
    check_correct_id_format,
)
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class ConvertRouteDistanceIntoTime(Tool):
    "Helper Tool: converts distance (in kilometer) into time (minutes) needed along a specific route alternative and vice versa."

    @staticmethod
    def invoke(
        route_id: str,
        time_minutes: Optional[float] = None,
        distance_km: Optional[float] = None,
    ) -> str:
        """
        Args:
            route_id (str): The specific route_id for the alternative to use for conversion.
            time_minutes (Optional[float]): The time in minutes to convert into distance along this route.
            distance_km (Optional[float]): The distance in kilometer to convert into time along this route.
        Returns:
            str: JSON string containing status, result/errors.
        """
        response = {}

        # --- Error Handling ---
        if not check_correct_id_format(route_id, "route"):
            response["status"] = "FAILURE"
            error_message = "ConvertRouteDistanceIntoTime_001: Invalid request - Invalid route_id format."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CONVERT_RTDT_001": error_message}
            return json.dumps(response)

        if time_minutes is not None and distance_km is not None:
            response["status"] = "FAILURE"
            error_message = "ConvertRouteDistanceIntoTime_002: Invalid request - Only one of time_minutes or distance_km can be set."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CONVERT_RTDT_002": error_message}
            return json.dumps(response)

        if time_minutes is None and distance_km is None:
            response["status"] = "FAILURE"
            error_message = "ConvertRouteDistanceIntoTime_003: Invalid request - Either time_minutes or distance_km must be set."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CONVERT_RTDT_003": error_message}
            return json.dumps(response)

        # --- Get Route Data using DataManager ---
        # Access the shared DataManager instance
        route_data = car_va_data_manager.get_route_by_id(route_id)

        if route_data is None:
            response["status"] = "FAILURE"
            error_message = f"ConvertRouteDistanceIntoTime_004: Invalid parameter - route_id '{route_id}' not found."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CONVERT_RTDT_004": error_message}
            return json.dumps(response)

        # --- Perform Conversion using the FLAT route_data structure ---
        try:
            # Extract data directly from the flat dictionary
            duration_route_minutes = float(
                route_data.get("duration_hours", 0)
            ) * 60 + float(route_data.get("duration_minutes", 0))
            distance_route_km = float(route_data.get("distance_km", 0))

            # Basic check for valid route data (avoid division by zero)
            if duration_route_minutes <= 0 or distance_route_km <= 0:
                response["status"] = "FAILURE"
                error_message = f"ConvertRouteDistanceIntoTime_011: Invalid route data for '{route_id}': zero or negative distance/duration."
                tool_execution_errors_during_runtime.get().append(error_message)
                response["errors"] = {"CONVERT_RTDT_011": error_message}
                return json.dumps(response)

            if time_minutes is not None:
                # Convert time into distance
                if time_minutes > duration_route_minutes:
                    response["status"] = "FAILURE"
                    error_message = f"ConvertRouteDistanceIntoTime_005: Requested time_minutes ({time_minutes}) exceeds the total duration ({duration_route_minutes:.1f} mins) of route {route_id}."
                    tool_execution_errors_during_runtime.get().append(error_message)
                    response["errors"] = {"CONVERT_RTDT_005": error_message}
                    return json.dumps(response)

                # Proportional calculation
                calculated_distance_km = (
                    time_minutes / duration_route_minutes
                ) * distance_route_km
                response["status"] = "SUCCESS"
                response["result"] = {"distance_km": round(calculated_distance_km, 1)}

            elif distance_km is not None:
                # Convert distance into time
                if distance_km > distance_route_km:
                    response["status"] = "FAILURE"
                    error_message = f"ConvertRouteDistanceIntoTime_006: Requested distance_km ({distance_km}) exceeds the total distance ({distance_route_km:.1f} km) of route {route_id}."
                    tool_execution_errors_during_runtime.get().append(error_message)
                    response["errors"] = {"CONVERT_RTDT_006": error_message}
                    return json.dumps(response)

                # Proportional calculation
                calculated_time_minutes = (
                    distance_km / distance_route_km
                ) * duration_route_minutes
                response["status"] = "SUCCESS"
                response["result"] = {"time_minutes": round(calculated_time_minutes, 1)}

        except (TypeError, ValueError, KeyError) as e:
            # Catch potential errors if route_data is missing keys or has invalid types
            response["status"] = "FAILURE"
            error_message = f"ConvertRouteDistanceIntoTime_007: Error processing route data for '{route_id}': {e}"
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"CONVERT_RTDT_ERR": error_message}
            return json.dumps(response)

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "convert_route_distance_and_time",
                "description": "Helper Tool: converts distance (in kilometer) into time (minutes) needed along specific route and vice versa.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": [
                        "route_id",
                    ],
                    "properties": {
                        "route_id": {
                            "type": "string",
                            "description": "The route_id for which conversion should happen.",
                        },
                        "time_minutes": {
                            "type": "integer",
                            "description": "The time in minutes to convert into distance.",
                        },
                        "distance_km": {
                            "type": "integer",
                            "description": "The distance in kilometer to convert into time.",
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
                "distance_km": {
                    "type": "number",
                    "description": "The distance in kilometers calculated from the given time. Output present if time_minutes was given.",
                    "examples": [15.5],
                },
                "time_minutes": {
                    "type": "number",
                    "description": "The time in minutes calculated from the given distance. Output present if distance_km was given.",
                    "examples": [20.0],
                },
            },
            "required": [],
            "additionalProperties": False,
        }
