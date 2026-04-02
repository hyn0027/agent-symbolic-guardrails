import json
from typing import Any, Dict, List, Optional

# --- Shared DataManager ---
from dataset_domains.CarBench.mock_data import car_va_data_manager

# --- Helper Functions ---
from dataset_domains.CarBench.mock_data.data_manager import read_jsonl_file
from dataset_domains.CarBench.tools.helper_functions import (
    check_correct_id_format,
)
from dataset_domains.CarBench.tools.navigation.helper_functions import (
    apply_filters,
    is_near_start_or_destination,
    is_point_near_route,
)

# --- Base Tool Class ---
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class SearchPoiAlongTheRoute(Tool):
    """
    Points of Interest Search: Searches for points of interest of a specified category
    that are geometrically close to a given route. Calculates the detour distance
    and time for up to 3 POIs with the smallest detour. Information includes name,
    position, detour, opening hours, and phone number.
    """

    name = "search_poi_along_the_route"

    @staticmethod
    def invoke(
        route_id: str,
        category_poi: str,
        at_kilometer: Optional[int] = None,
        filters: Optional[List[str]] = None,
    ) -> str:
        """
        Args:
            route_id (str): The ID of the main route (Loc->Loc, Loc->POI, or POI->Loc).
            category_poi (str): The category of the point of interest to search for.
            at_kilometer (Optional[int]): The kilometer mark along the route to focus the search around
                                        (within a +/- 10 km radius). If None, searches along the whole route.
            filters (Optional[List[str]]): List of filter strings to apply to search results.
        Returns:
            str: JSON string containing status, result (list of top POIs with detour info), or errors.
        """
        response = {}
        # Configuration
        _max_results = 3
        _segment_length_at_km = 25

        # --- Check if DataManager is available ---
        if car_va_data_manager is None:
            error_message = (
                "SearchPoiAlongTheRoute_001: Core Data Manager failed to initialize."
            )
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SEARCH_POI_ATR_001": error_message}
            return json.dumps(response)

        # --- Validate Inputs ---
        if not check_correct_id_format(route_id, "route"):
            error_message = "SearchPoiAlongTheRoute_002: Invalid route_id format."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SEARCH_POI_ATR_002": error_message}
            return json.dumps(response)
        if not category_poi or not isinstance(category_poi, str):
            error_message = "SearchPoiAlongTheRoute_003: Invalid category_poi provided."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SEARCH_POI_ATR_003": error_message}
            return json.dumps(response)

        # --- If category is charging_station, then at_kilometer is required
        if category_poi.strip().lower() == "charging_stations":
            if at_kilometer is None:
                error_message = "SearchPoiAlongTheRoute_007: 'at_kilometer' is required when searching for charging_station POIs."
                tool_execution_errors_during_runtime.get().append(error_message)
                response["errors"] = {"SEARCH_POI_ATR_007": error_message}
                return json.dumps(response)

        # --- Get Main Route Data ---
        main_route_data = car_va_data_manager.get_route_by_id(route_id)
        if main_route_data is None:
            error_message = (
                f"SearchPoiAlongTheRoute_004: Route with ID '{route_id}' not found."
            )
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SEARCH_POI_ATR_004": error_message}
            return json.dumps(response)

        # Extract main route details
        try:
            main_route_start_id = main_route_data["start_id"]
            main_route_dest_id = main_route_data["destination_id"]
            main_route_dist_km = float(main_route_data.get("distance_km", 0.0))
            main_route_hours = int(main_route_data.get("duration_hours", 0))
            main_route_minutes = int(main_route_data.get("duration_minutes", 0))
            main_route_total_minutes = (main_route_hours * 60) + main_route_minutes
        except (KeyError, ValueError, TypeError) as e:
            error_message = f"SearchPoiAlongTheRoute_005: Could not parse main route data for '{route_id}': {e}."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SEARCH_POI_ATR_005": error_message}
            return json.dumps(response)

        # --- Skip if not a Loc->Loc route ---
        if not main_route_start_id.startswith(
            "loc_"
        ) or not main_route_dest_id.startswith("loc_"):
            error_message = f"SearchPoiAlongTheRoute_006: This function only supports POI searches for location->location routes."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SEARCH_POI_ATR_006": error_message}
            return json.dumps(response)

        # --- OPTIMIZED APPROACH: Use corresponding_route_ids for direct lookup ---
        # Find POIs directly by category and corresponding route IDs
        # print(
            # f"DEBUG: Finding POIs of category '{category_poi}' that correspond to route '{route_id}'..."
        # )

        potential_pois = []
        category_poi_exists = False

        for poi_id, poi_data in car_va_data_manager.pois.items():
            # Check category first
            if poi_data.get("category") == category_poi:
                category_poi_exists = True

                # Check if this POI has corresponding_route_ids and if our route is included
                if "corresponding_route_ids" in poi_data:
                    corresponding_routes = poi_data["corresponding_route_ids"]
                    if route_id in corresponding_routes:
                        # This POI is directly associated with our route
                        potential_poi = poi_data.copy()

                        # If at_kilometer is specified, we might want to filter further
                        if at_kilometer is not None:
                            if "route_positions" in potential_poi:
                                direction = route_id[:11]
                                poi_km = potential_poi["route_positions"][direction][
                                    "at_route_kilometer"
                                ]
                                # Skip if POI is outside our search window
                                if abs(poi_km - at_kilometer) > _segment_length_at_km:
                                    continue
                            # If POI doesn't have kilometer info, still include it

                        potential_pois.append(potential_poi)

        if not category_poi_exists:
            error_message = f"SearchPoiAlongTheRoute_007: Invalid category requested ('{category_poi}') or no POIs exist for this category."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"SEARCH_POI_ATR_007": error_message}
            return json.dumps(response)

        if not potential_pois:
            response["status"] = "SUCCESS"
            response["result"] = {f"pois_found_along_route": []}
            return json.dumps(response)

        # --- Calculate Detours using DataManager Route Methods ---
        pois_with_detour = []
        # print(f"DEBUG: Calculating detours for {len(potential_pois)} potential POIs...")

        for poi in potential_pois:
            poi_id = poi["id"]

            # Use DataManager to get routes
            routes_to_poi = car_va_data_manager.get_routes_location_to_poi(
                main_route_start_id, poi_id
            )
            routes_from_poi = car_va_data_manager.get_routes_poi_to_location(
                poi_id, main_route_dest_id
            )

            if not routes_to_poi or not routes_from_poi:
                # Skip if either route segment is unavailable
                continue

            # Use the route where base_route_id matches the main route_id
            route_sp = next(
                (r for r in routes_to_poi if r.get("base_route_id") == route_id), None
            )
            route_pd = next(
                (r for r in routes_from_poi if r.get("base_route_id") == route_id), None
            )
            if route_sp is None or route_pd is None:
                response["status"] = "FAILURE"
                response["errors"] = {
                    "SEARCH_POI_ATR_005": f"Could not find valid route segments for POI '{poi_id}' along route '{route_id}'."
                }
                return json.dumps(response)

            try:
                # Calculate detour information
                sp_dist = float(route_sp.get("distance_km", 0.0))
                sp_hours = int(route_sp.get("duration_hours", 0))
                sp_mins = int(route_sp.get("duration_minutes", 0))
                sp_total_mins = (sp_hours * 60) + sp_mins

                pd_dist = float(route_pd.get("distance_km", 0.0))
                pd_hours = int(route_pd.get("duration_hours", 0))
                pd_mins = int(route_pd.get("duration_minutes", 0))
                pd_total_mins = (pd_hours * 60) + pd_mins

                detour_km = max(0.0, sp_dist + pd_dist - main_route_dist_km)
                detour_total_minutes = max(
                    0, sp_total_mins + pd_total_mins - main_route_total_minutes
                )

                detour_time_hour = detour_total_minutes // 60
                detour_time_minutes = detour_total_minutes % 60

                poi["detour_from_route_km"] = {
                    "detour": round(detour_km, 1),
                    "unit": "km",
                }
                poi["detour_from_route_time"] = {
                    "hour": detour_time_hour,
                    "minutes": detour_time_minutes,
                }
                pois_with_detour.append(poi)

            except (KeyError, ValueError, TypeError) as e:
                # print(
                    # f"Warning: Error processing route data for POI {poi_id}: {e}. Skipping."
                # )
                continue

        # --- Apply Filters if Provided ---
        if filters:
            try:
                pois_with_detour = apply_filters(pois_with_detour, filters)
            except ValueError as e:
                response["status"] = "FAILURE"
                response["errors"] = {
                    "SEARCH_POI_ATR_006": f"Error applying filters: {str(e)}"
                }
                return json.dumps(response)

        # --- Sort by Detour Time or Distance and Select Top Results ---
        if filters and "any::sort_by_distance" in filters:
            pois_with_detour.sort(key=lambda x: x["detour_from_route_km"]["detour"])
        else:
            # Default sort by detour time
            pois_with_detour.sort(
                key=lambda x: x["detour_from_route_time"]["hour"] * 60
                + x["detour_from_route_time"]["minutes"]
            )

        top_pois = pois_with_detour[:_max_results]

        # --- Format Success Response ---
        response["status"] = "SUCCESS"
        response["result"] = {f"pois_found_along_route": top_pois}

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "search_poi_along_the_route",
                "description": "Points of Interest Search: searches for points of interest in the specified category along the specified route. Points of interest information includes name, position (long, lat), detour from route in km, detour from route in hour and minutes, opening hours, and phone number. Returns 3 points of interest with the smallest detour time (sorting can be changed to smallest detour distance with filter).",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["route_id", "category_poi"],
                    "properties": {
                        "route_id": {
                            "type": "string",
                            "description": "The route_id to search for points of interest along the route.",
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
                        "at_kilometer": {
                            "type": "integer",
                            "description": "at what kilometer of the route to look for the place (with radius of 10 km). If not set, search is done along whole route. This parameter is required if category_poi is charging_stations.",
                        },
                        "filters": {
                            "type": "array",
                            "description": "List of filter strings to apply to search results. any:: filters can be applied to all categories, charging_stations:: filters can be applied only if category is charging stations. Default sorting is by detour time.",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "any::currently_open",
                                    "any::sort_by_distance",
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
                "pois_found_along_route": {
                    "type": "array",
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
                                "examples": ["00:00h - 24:00h"],
                            },
                            "phone_number": {
                                "type": "string",
                                "description": "Contact phone number of the point of interest.",
                                "examples": ["+49 123 456789"],
                            },
                            "corresponding_location_id": {
                                "type": "string",
                                "description": "The ID of the corresponding location.",
                                "examples": ["loc_che_4105"],
                            },
                            "charging_plugs": {
                                "type": "array",
                                "description": "List of charging plugs available at the point of interest. Only present if category is 'charging_stations'.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "plug_id": {
                                            "type": "string",
                                            "description": "The ID of the charging plug. Only present if category is 'charging_stations'.",
                                            "examples": ["plg_cha_5499"],
                                        },
                                        "power_type": {
                                            "type": "string",
                                            "description": "The type of power for the charging plug. Only present if category is 'charging_stations'.",
                                            "examples": ["AC", "DC"],
                                        },
                                        "power_kw": {
                                            "type": "number",
                                            "description": "Power output in kilowatts. Only present if category is 'charging_stations'.",
                                            "examples": [22.0],
                                        },
                                        "availability": {
                                            "type": "string",
                                            "description": "Availability status of the charging plug. Only present if category is 'charging_stations'.",
                                            "examples": [
                                                "available",
                                                "occupied",
                                                "maintenance",
                                            ],
                                        },
                                    },
                                },
                            },
                            "at_route_kilometer": {
                                "type": "float",
                                "description": "The kilometer mark along the route where the point of interest is located.",
                                "examples": [12.5],
                            },
                            "detour_from_route_km": {
                                "type": "object",
                                "description": "Detour distance from the route to the point of interest.",
                                "properties": {
                                    "detour": {
                                        "type": "number",
                                        "description": "The detour distance in kilometers.",
                                        "examples": [1.5],
                                    },
                                    "unit": {
                                        "type": "string",
                                        "description": "The unit of measurement for the detour.",
                                        "examples": ["km"],
                                    },
                                },
                            },
                            "detour_from_route_time": {
                                "type": "object",
                                "description": "Detour time to reach the point of interest.",
                                "properties": {
                                    "hour": {
                                        "type": "integer",
                                        "description": "Detour time in hours.",
                                        "examples": [0],
                                    },
                                    "minutes": {
                                        "type": "integer",
                                        "description": "Detour time in minutes.",
                                        "examples": [15],
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
                    "description": "List of points of interest found along the route.",
                }
            },
            "required": ["pois_found_along_route"],
            "additionalProperties": False,
        }
