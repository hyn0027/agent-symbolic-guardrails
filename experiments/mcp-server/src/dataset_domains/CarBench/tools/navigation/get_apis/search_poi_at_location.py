import json
from typing import Any, Dict, List, Optional

from dataset_domains.CarBench.mock_data import car_va_data_manager
from dataset_domains.CarBench.tools.helper_functions import (
    check_correct_id_format,
)
from dataset_domains.CarBench.tools.navigation.helper_functions import (
    apply_filters,
)
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class SearchPoiAtLocation(Tool):
    """
    Points of Interest Search: Searches for points of interest (POIs) of a specified
    category that are associated with a given location ID. POI information includes
    name, position, opening hours, phone number, etc.
    """

    name = "search_poi_at_location"  # Tool name

    @staticmethod
    def invoke(
        location_id: str,
        category_poi: str,
        filters: Optional[List[str]] = None,
    ) -> str:
        """
        Args:
            location_id (str): The ID of the location around which to search for POIs (e.g., 'loc_mun_1234').
            category_poi (str): The category of the point of interest to search for.
            filters (Optional[List[str]]): List of filter strings to apply to search results.

        Returns:
            str: JSON string containing status, result (list of POIs found), or errors.
        """
        response = {}

        # --- Validate Inputs ---
        # Ensure location_id is specifically a location ID format
        if not check_correct_id_format(
            location_id, "poi_or_location"
        ):  # Use specific type if helper supports it
            # Or check prefix directly: if not location_id.startswith("loc_"):
            response["status"] = "FAILURE"
            error_message = f"SearchPoiAtLocation_001: Invalid location_id format '{location_id}'. Must be a location ID."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SEARCH_POI_AT_LOC_001": error_message}
            return json.dumps(response)

        if not category_poi or not isinstance(category_poi, str):
            response["status"] = "FAILURE"
            response["errors"] = {
                "SEARCH_POI_AT_LOC_003": "Invalid category_poi provided."
            }
            return json.dumps(response)

        # --- Get POIs associated with the Location ID using DataManager ---
        # This method uses the cached POIs for efficiency
        try:
            all_pois_at_location = car_va_data_manager.get_pois_for_location(
                location_id
            )
        except Exception as e:
            # Catch potential errors during cache access, though less likely
            # print(f"ERROR accessing POIs for location '{location_id}': {e}")
            response["status"] = "FAILURE"
            error_message = f"SearchPoiAtLocation_002: Error retrieving POIs for location '{location_id}'."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SEARCH_POI_AT_LOC_002": error_message}
            return json.dumps(response)

        # --- Filter the results by the requested category ---
        category_pois = [
            poi for poi in all_pois_at_location if poi.get("category") == category_poi
        ]

        # --- Apply Filters if provided ---
        if filters:
            try:
                category_pois = apply_filters(category_pois, filters)
            except Exception as e:
                # Handle any errors that occur during filtering
                response["status"] = "FAILURE"
                error_message = (
                    f"SearchPoiAtLocation_003: Error applying filters: {str(e)}"
                )
                tool_execution_errors_during_runtime.get().append(error_message)
                response["errors"] = {"SEARCH_POI_AT_LOC_003": error_message}
                return json.dumps(response)

        # --- Handle Results ---
        if not category_pois:
            # Check if the location itself exists to provide a better error message
            location_exists = (
                car_va_data_manager.get_location_by_id(location_id) is not None
            )
            if not location_exists:
                error_msg = f"Location with ID '{location_id}' not found."
                error_message = f"SearchPoiAtLocation_004: {error_msg}"
                tool_execution_errors_during_runtime.get().append(error_message)
                response["errors"] = {"SEARCH_POI_AT_LOC_004": error_message}
                return json.dumps(response)

        # Found POIs of the specified category for the location
        response["status"] = "SUCCESS"
        # Return the list of matching POI dictionaries
        response["result"] = {"pois_found": category_pois}
        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "search_poi_at_location",
                "description": "Points of Interest Search: searches for points of interest in the specified category around the specified location. Points of interest information includes name, position (long, lat), distance from location in km, duration from location in hour and minutes, opening hours, and phone number.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["location_id", "category_poi"],
                    "properties": {
                        "location_id": {
                            "type": "string",
                            "description": "The location 'id' to search for a POI",
                        },
                        "category_poi": {
                            "type": "string",
                            "description": "The category of the point of interest to search for.",
                            "enum": [
                                "airports",
                                "bakery",
                                "fast_food",
                                "parking",
                                "public_toilets",
                                "restaurants",
                                "supermarkets",
                                "charging_stations",
                            ],
                        },
                        "filters": {
                            "type": "array",
                            "description": "List of filter strings to apply to search results. any:: filters can be applied to all categories, charging_stations:: filters can be applied only if category is charging stations.",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "any::currently_open",
                                    "charging_stations::has_available_plug",
                                    "charging_stations::has_dc_plug",
                                ],
                            },
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
                "pois_found": {
                    "type": "array",
                    "description": "List of points of interest found for the given location and category.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "The ID of the point of interest.",
                                "examples": ["poi_caf_7173"],
                            },
                            "name": {
                                "type": "string",
                                "description": "The name of the point of interest.",
                                "examples": ["Local Cafe"],
                            },
                            "category": {
                                "type": "string",
                                "description": "The category of the point of interest.",
                                "examples": ["cafe"],
                            },
                            "position": {
                                "type": "object",
                                "description": "The geographical position of the point of interest.",
                                "properties": {
                                    "latitude": {
                                        "type": "number",
                                        "description": "Latitude of the point of interest.",
                                        "examples": [48.1375],
                                    },
                                    "longitude": {
                                        "type": "number",
                                        "description": "Longitude of the point of interest.",
                                        "examples": [11.575],
                                    },
                                },
                            },
                            "opening_hours": {
                                "type": "string",
                                "description": "Opening hours of the point of interest.",
                                "examples": ["08:00h - 20:00h"],
                            },
                            "phone_number": {
                                "type": "string",
                                "description": "Contact phone number of the point of interest.",
                                "examples": ["+49 123 456789"],
                            },
                            "corresponding_location_id": {
                                "type": "string",
                                "description": "The ID of the location to which the POI is associated.",
                                "examples": ["loc_mun_1234"],
                            },
                            "charging_plugs": {
                                "type": "array",
                                "description": "List of charging plugs available at the point of interest. Output present if input variable category_poi was set to 'charging_stations'.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "plug_id": {
                                            "type": "string",
                                            "description": "The ID of the charging plug.",
                                            "examples": ["plg_cha_5499"],
                                        },
                                        "power_type": {
                                            "type": "string",
                                            "description": "The type of power for the charging plug.",
                                            "examples": ["AC", "DC"],
                                        },
                                        "power_kw": {
                                            "type": "number",
                                            "description": "Power output in kilowatts.",
                                            "examples": [22.0],
                                        },
                                        "availability": {
                                            "type": "string",
                                            "description": "Availability status of the charging plug.",
                                            "examples": [
                                                "available",
                                                "occupied",
                                                "maintenance",
                                            ],
                                        },
                                    },
                                },
                            },
                        },
                        "required": [
                            "id",
                            "name",
                            "category",
                            "position",
                            "opening_hours",
                            "phone_number",
                            "corresponding_location_id",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["pois_found"],
            "additionalProperties": False,
        }
