import json
from typing import Any, Dict, Union

from dataset_domains.CarBench.context.fixed_context import fixed_context
from dataset_domains.CarBench.mock_data import car_va_data_manager
from dataset_domains.CarBench.policy_evaluator import policy_errors_during_runtime
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class GetWeather(Tool):
    "Weather Information: gets the weather information for the specified location and the specified time plus the next time slot. Weather information includes temperature, wind speed, humidity, and condition (sunny, cloudy, rainy, foggy, etc.)"

    @staticmethod
    def invoke(
        location_or_poi_id: str,
        month: int,
        day: int,
        time_hour_24hformat: int,
        time_minutes: int = 0,
    ) -> str:
        """
        Args:
            location_id (str): The location to get the weather information.
            time (dict): The time to get the weather information.
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): Weather information for the specified location and time slot plus the next time slot.
            errors (dict): Error messages if the tool call was a "FAILURE".
        """
        response = {}
        fixed_ctx = fixed_context.get()

        if (
            month != fixed_ctx.current_datetime.month
            or day != fixed_ctx.current_datetime.day
        ):
            response["status"] = "FAILURE"
            error_message = (
                "AUT-POL:024: The weather can only be requested for the current day."
            )
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_WEATHER_001": error_message}
            policy_errors_during_runtime.get().append(error_message)
            return json.dumps(response)

        weather_location = car_va_data_manager.get_weather_for_point(location_or_poi_id)
        if weather_location is None:
            response["status"] = "FAILURE"
            error_message = (
                "GetWeather_002: Invalid location requested - location not found."
            )
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_WEATHER_002": error_message}
            return json.dumps(response)

        current_time_str = f"{time_hour_24hformat:02d}:{time_minutes:02d}"
        current_time_flt = float(current_time_str.replace(":", "."))
        for i, slot in enumerate(weather_location["weather"]):
            if (
                int(slot["start_time"].split(":")[0])
                <= current_time_flt
                < int(slot["end_time"].split(":")[0])
            ):
                current_slot = slot
                next_slot = (
                    weather_location[i + 1] if i + 1 < len(weather_location) else None
                )
                break

        response["status"] = "SUCCESS"
        response["result"] = {"current_slot": current_slot, "next_slot": next_slot}

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """
        Tool description visible to LLM.
        """

        return {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Weather Information: gets the weather information for the specified location and the specified time (3h slot) plus the next time slot. Weather information includes temperature, wind speed, humidity, and condition (sunny, cloudy, rainy, foggy, etc.)",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": [
                        "location_or_poi_id",
                        "month",
                        "day",
                        "time_hour_24hformat",
                    ],
                    "properties": {
                        "location_or_poi_id": {
                            "type": "string",
                            "description": "The location 'id' or point of interest (POI) 'id' to get the weather information",
                        },
                        "month": {
                            "type": "number",
                            "description": "The month to get the weather information.",
                            "multipleOf": 1,
                            "minimum": 1,
                            "maximum": 12,
                        },
                        "day": {
                            "type": "number",
                            "description": "The day to get the weather information.",
                            "multipleOf": 1,
                            "minimum": 1,
                            "maximum": 31,
                        },
                        "time_hour_24hformat": {
                            "type": "number",
                            "description": "The time hour to get the weather information.",
                            "multipleOf": 1,
                            "minimum": 0,
                            "maximum": 23,
                        },
                        "time_minutes": {
                            "type": "number",
                            "description": "The time minutes to get the weather information.",
                            "default": 0,
                            "multipleOf": 1,
                            "minimum": 0,
                            "maximum": 59,
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
        slot_schema = {
            "type": "object",
            "properties": {
                "start_time": {
                    "type": "string",
                    "description": "The starting time of the weather slot in HH:MM format.",
                    "examples": ["09:00"],
                },
                "end_time": {
                    "type": "string",
                    "description": "The ending time of the weather slot in HH:MM format.",
                    "examples": ["12:00"],
                },
                "temperature_c": {
                    "type": "number",
                    "description": "The temperature in Celsius during the slot.",
                    "examples": [1],
                },
                "wind_speed_kph": {
                    "type": "number",
                    "description": "The wind speed in kilometers per hour during the slot.",
                    "examples": [4],
                },
                "humidity_percent": {
                    "type": "number",
                    "description": "The humidity percentage during the slot.",
                    "examples": [68],
                },
                "condition": {
                    "type": "string",
                    "description": "The weather condition during the slot (e.g., sunny, cloudy, rainy, foggy, etc.).",
                    "examples": ["partly_cloudy"],
                },
            },
            "required": [
                "start_time",
                "end_time",
                "temperature_c",
                "wind_speed_kph",
                "humidity_percent",
                "condition",
            ],
            "additionalProperties": False,
        }

        return {
            "type": "object",
            "properties": {
                "current_slot": {
                    "type": ["object", "null"],
                    "description": "The weather information slot that covers the specified time.",
                    "allOf": [slot_schema],
                },
                "next_slot": {
                    "type": ["object", "null"],
                    "description": "The weather information slot immediately following the current slot. May be null if there is no subsequent time slot available.",
                    "allOf": [slot_schema],
                },
            },
            "required": ["current_slot", "next_slot"],
            "additionalProperties": False,
        }
