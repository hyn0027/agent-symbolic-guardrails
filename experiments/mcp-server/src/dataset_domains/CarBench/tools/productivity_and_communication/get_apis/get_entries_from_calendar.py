import json
from typing import Any, Dict, Union

from dataset_domains.CarBench.context.fixed_context import fixed_context
from dataset_domains.CarBench.mock_data import car_va_data_manager
from dataset_domains.CarBench.tasks.task_config import task_config
from dataset_domains.CarBench.policy_evaluator import policy_errors_during_runtime
from dataset_domains.CarBench.tools.tool import Tool
from dataset_domains.CarBench.tools.tool_execution_error_evaluator import (
    tool_execution_errors_during_runtime,
)


class GetEntriesFromCalendar(Tool):
    "Calendar Information: gets the entries (including meetings, events, etc.) set in the calendar from the current day. Returns entry start, duration, topic, and attendees."

    @staticmethod
    def invoke(month: int, day: int) -> str:
        """
        Returns:
            status (str): Indicates if the tool call was a "SUCCESS" or "FAILURE".
            result (dict): The entries set in the calendar from the current day. Includes entry start, duration, topic, and attendees.
            errors (dict): Error messages if the tool call was a "FAILURE".
        """
        response = {}
        fixed_ctx = fixed_context.get()

        if (
            month != fixed_ctx.current_datetime.month
            or day != fixed_ctx.current_datetime.day
        ):
            response["status"] = "FAILURE"
            error_message = "AUT-POL:023: The calendar entries can only be requested for the current day."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_ENTRIES_FROM_CALENDAR_001": error_message}
            policy_errors_during_runtime.get().append(error_message)
            return json.dumps(response)
        task_config_data = task_config.get()
        try:
            calendar_data = car_va_data_manager.get_calendar_line(
                task_config_data.calendar_id
            )
        except KeyError:
            response["status"] = "FAILURE"
            error_message = f"GetEntriesFromCalendar_002: Calendar with ID {task_config_data.calendar_id} not found."
            tool_execution_errors_during_runtime.get().append(error_message)
            response["errors"] = {"GET_ENTRIES_FROM_CALENDAR_002": error_message}
            return json.dumps(response)

        response["status"] = "SUCCESS"
        response["result"] = {
            "date": calendar_data["date"],
            "meetings": calendar_data["meetings"],
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
                "name": "get_entries_from_calendar",
                "description": "Calendar Information: gets the entries (including meetings, events, appointment etc.) set in the calendar from the current day. Returns the entry start, duration, topic, and attendees.",
                # "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["month", "day"],
                    "properties": {
                        "month": {
                            "type": "integer",
                            "description": "The month for which the calendar entries are requested.",
                        },
                        "day": {
                            "type": "integer",
                            "description": "The day for which the calendar entries are requested.",
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
                "date": {
                    "type": "object",
                    "description": "The calendar date for which the entries are retrieved.",
                    "properties": {
                        "year": {
                            "type": "integer",
                            "description": "Year of the calendar date.",
                            "examples": [2025],
                        },
                        "month": {
                            "type": "integer",
                            "description": "Month of the calendar date.",
                            "examples": [2],
                        },
                        "day": {
                            "type": "integer",
                            "description": "Day of the calendar date.",
                            "examples": [14],
                        },
                    },
                    "required": ["year", "month", "day"],
                    "additionalProperties": False,
                },
                "meetings": {
                    "type": "array",
                    "description": "List of calendar entries for the current day. Each entry includes the start time, duration, location, attendees, and meeting topic.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "start": {
                                "type": "object",
                                "description": "The start time of the meeting.",
                                "properties": {
                                    "hour": {
                                        "type": "string",
                                        "description": "The hour when the meeting starts.",
                                        "examples": ["13"],
                                    },
                                    "minute": {
                                        "type": "string",
                                        "description": "The minute when the meeting starts.",
                                        "examples": ["30"],
                                    },
                                },
                                "required": ["hour", "minute"],
                                "additionalProperties": False,
                            },
                            "duration": {
                                "type": ["string", "number"],
                                "description": "The duration of the meeting. This can be provided either as a string (e.g., '30min') or as a number (e.g., 30).",
                                "examples": ["30min"],
                            },
                            "location": {
                                "type": "string",
                                "description": "The location of the meeting.",
                                "examples": ["Pforzheim"],
                            },
                            "attendees": {
                                "type": "array",
                                "description": "List of contact IDs representing the meeting attendees.",
                                "items": {
                                    "type": "string",
                                    "description": "Contact ID for an attendee.",
                                    "examples": ["con_5791"],
                                },
                                "examples": [
                                    ["con_5791", "con_3673", "con_4352", "con_2885"]
                                ],
                            },
                            "topic": {
                                "type": "string",
                                "description": "The topic or title of the meeting.",
                                "examples": ["Strategy Planning"],
                            },
                        },
                        "required": [
                            "start",
                            "duration",
                            "location",
                            "attendees",
                            "topic",
                        ],
                        "additionalProperties": False,
                    },
                    "examples": [
                        [
                            {
                                "start": {"hour": "13", "minute": "30"},
                                "duration": "30min",
                                "location": "Pforzheim",
                                "attendees": [
                                    "con_5791",
                                    "con_3673",
                                    "con_4352",
                                    "con_2885",
                                ],
                                "topic": "Strategy Planning",
                            },
                            {
                                "start": {"hour": "17", "minute": "30"},
                                "duration": 30,
                                "location": "Hannover",
                                "attendees": [
                                    "con_8073",
                                    "con_2923",
                                    "con_5525",
                                    "con_5532",
                                ],
                                "topic": "Brand Positioning",
                            },
                        ]
                    ],
                },
            },
            "required": ["date", "meetings"],
            "additionalProperties": False,
        }
