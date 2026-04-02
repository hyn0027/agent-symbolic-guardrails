import json
from typing import Any, Dict

from dataset_domains.CarBench.context.fixed_context import fixed_context
from dataset_domains.CarBench.tools.tool import Tool


class GetUserPreferences(Tool):
    """Tool to retrieve user preferences based on specified categories."""

    @staticmethod
    def invoke(preference_categories: Dict[str, Dict[str, bool]]) -> str:
        """
        Retrieves user preferences based on specified categories and subcategories.

        Args:
            data: The request data
            preference_categories: Dictionary containing categories and subcategories to retrieve
                                  Format: {category: {subcategory: True}}

        Returns:
            JSON string containing the requested user preferences
        """
        response = {}
        # Get the environment context
        fixed_ctx = fixed_context.get()

        user_preferences = fixed_ctx.user_preferences

        # Extract only the requested preferences
        relevant_preferences = {}

        for category, subcategories in preference_categories.items():
            if hasattr(user_preferences, category):
                category_prefs = getattr(user_preferences, category)
                relevant_preferences[category] = {}

                for subcategory, is_requested in subcategories.items():
                    if is_requested and hasattr(category_prefs, subcategory):
                        relevant_preferences[category][subcategory] = getattr(
                            category_prefs, subcategory
                        )

        response["status"] = "SUCCESS"
        response["result"] = relevant_preferences
        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """
        return {
            "type": "function",
            "function": {
                "name": "get_user_preferences",
                "description": "Retrieves user preferences for one or more specified categories and subcategories",
                "parameters": {
                    "type": "object",
                    "required": ["preference_categories"],
                    "properties": {
                        "preference_categories": {
                            "type": "object",
                            "description": "Categories of preferences to check for",
                            "properties": {
                                "points_of_interest": {
                                    "type": "object",
                                    "description": "Points of interest preference categories",
                                    "properties": {
                                        "airports": {
                                            "type": "boolean",
                                            "description": "If information about user's preferred airports is required",
                                        },
                                        "bakery": {
                                            "type": "boolean",
                                            "description": "If information about user's preferred bakeries is required",
                                        },
                                        "fast_food": {
                                            "type": "boolean",
                                            "description": "If information about user's preferred fast food restaurants is required",
                                        },
                                        "parking": {
                                            "type": "boolean",
                                            "description": "If information about user's preferred parking options is required",
                                        },
                                        "public_toilets": {
                                            "type": "boolean",
                                            "description": "If information about user's preferred public toilets is required",
                                        },
                                        "restaurants": {
                                            "type": "boolean",
                                            "description": "If information about user's preferred restaurants is required",
                                        },
                                        "supermarkets": {
                                            "type": "boolean",
                                            "description": "If information about user's preferred supermarkets is required",
                                        },
                                        "charging_stations": {
                                            "type": "boolean",
                                            "description": "If information about user's preferred charging stations is required",
                                        },
                                    },
                                },
                                "navigation_and_routing": {
                                    "type": "object",
                                    "description": "Navigation and routing preference categories",
                                    "properties": {
                                        "route_selection": {
                                            "type": "boolean",
                                            "description": "If information about user's route selection preferences is required",
                                        }
                                    },
                                },
                                "vehicle_settings": {
                                    "type": "object",
                                    "description": "Vehicle settings preference categories",
                                    "properties": {
                                        "climate_control": {
                                            "type": "boolean",
                                            "description": "If information about user's climate control preferences is required",
                                        },
                                        "vehicle_settings": {
                                            "type": "boolean",
                                            "description": "If information about user's general vehicle settings preferences is required",
                                        },
                                    },
                                },
                                "productivity_and_communication": {
                                    "type": "object",
                                    "description": "Productivity and communication preference categories",
                                    "properties": {
                                        "email": {
                                            "type": "boolean",
                                            "description": "If information about user's email preferences is required",
                                        },
                                        "calendar": {
                                            "type": "boolean",
                                            "description": "If information about user's calendar preferences is required",
                                        },
                                    },
                                },
                                "weather": {
                                    "type": "object",
                                    "description": "Weather preference categories",
                                    "properties": {
                                        "weather": {
                                            "type": "boolean",
                                            "description": "If information about user's weather preferences is required",
                                        }
                                    },
                                },
                            },
                        }
                    },
                    "additionalProperties": False,
                },
            },
        }
