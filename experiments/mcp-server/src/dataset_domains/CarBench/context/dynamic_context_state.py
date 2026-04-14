import contextvars
import threading
from enum import Enum
from typing import Union, List

from pydantic import BaseModel, Field, ValidationError, ConfigDict

from dataset_domains.CarBench.policy_evaluator import policy_errors_during_runtime

# A ContextVar that will hold the current VehicleContext for the running task.
context_state: contextvars.ContextVar["ContextState"] = contextvars.ContextVar(
    "context_state"
)


class AmbientLight(str, Enum):
    OFF = ("OFF",)
    RED = ("RED",)
    GREEN = ("GREEN",)
    BLUE = ("BLUE",)
    YELLOW = ("YELLOW",)
    WHITE = ("WHITE",)
    PINK = ("PINK",)
    ORANGE = ("ORANGE",)
    PURPLE = ("PURPLE",)
    CYAN = ("CYAN",)


class FanAirflowDirection(str, Enum):
    FEET = ("FEET",)
    HEAD = ("HEAD",)
    HEAD_FEET = ("HEAD_FEET",)
    WINDSHIELD = ("WINDSHIELD",)
    WINDSHIELD_FEET = ("WINDSHIELD_FEET",)
    WINDSHIELD_HEAD = ("WINDSHIELD_HEAD",)
    WINDSHIELD_HEAD_FEET = "WINDSHIELD_HEAD_FEET"


class AirCirculation(str, Enum):
    AUTO = ("AUTO",)
    FRESH_AIR = ("FRESH_AIR",)
    RECIRCULATION = "RECIRCULATION"


class ContextState(BaseModel):
    # dynamic based tools
    sunroof_position: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Sunroof opening percentage, 0 (closed) - 100 (open))",
    )
    sunshade_position: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Sunroof opening percentage, 0 (closed) - 100 (open))",
    )
    trunk_door_position: str = Field(
        default="closed", description="Trunk door position, closed or open"
    )
    window_driver_position: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Driver window opening percentage, 0 (closed) - 100 (open))",
    )
    window_passenger_position: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Passenger window opening percentage, 0 (closed) - 100 (open))",
    )
    window_driver_rear_position: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Passenger window opening percentage, 0 (closed) - 100 (open))",
    )
    window_passenger_rear_position: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Passenger window opening percentage, 0 (closed) - 100 (open))",
    )
    reading_light_driver: bool = Field(
        default=False, description="Reading light status for the driver"
    )
    reading_light_passenger: bool = Field(
        default=False, description="Reading light status for the passenger"
    )
    reading_light_driver_rear: bool = Field(
        default=False, description="Reading light status for the driver rear"
    )
    reading_light_passenger_rear: bool = Field(
        default=False, description="Reading light status for the passenger rear"
    )
    fog_lights: bool = Field(default=False, description="Fog lights status")
    head_lights_low_beams: bool = Field(
        default=False, description="Head lights low beam status"
    )
    head_lights_high_beams: bool = Field(
        default=False, description="Head lights high beam status"
    )
    ambient_light: AmbientLight = Field(
        default=AmbientLight.OFF, description="Color of the ambient lighting"
    )
    climate_temperature_driver: float = Field(
        default=20,
        ge=16,
        le=28,
        multiple_of=0.5,
        description="Climate temperature for the driver",
    )
    climate_temperature_passenger: float = Field(
        default=20,
        ge=16,
        le=28,
        multiple_of=0.5,
        description="Climate temperature for the passenger",
    )
    steering_wheel_heating: int = Field(
        default=0, ge=0, le=3, description="Steering wheel heating level"
    )
    seat_heating_driver: int = Field(
        default=0, ge=0, le=3, description="Heating level for the driver seat"
    )
    seat_heating_passenger: int = Field(
        default=0, ge=0, le=3, description="Heating level for the passenger seat"
    )
    fan_speed: int = Field(default=0, ge=0, le=5, description="Climate fan speed")
    window_front_defrost: bool = Field(
        default=False, description="Front window defrost status"
    )
    window_rear_defrost: bool = Field(
        default=False, description="Rear window defrost status"
    )
    fan_airflow_direction: FanAirflowDirection = Field(
        default=FanAirflowDirection.FEET, description="Fan airflow direction"
    )
    air_conditioning: bool = Field(default=False, description="Air conditioning status")
    air_circulation: AirCirculation = Field(
        default=AirCirculation.AUTO, description="Air circulation status"
    )

    # Navigation State
    navigation_active: bool = Field(
        default=False, description="Navigation active status"
    )
    waypoints_id: list[str] = Field(
        default_factory=list,
        description="Waypoint IDs for the navigation, including the start ID and the final destination ID",
    )
    routes_to_final_destination_id: list[str] = Field(
        default_factory=list,
        description="Current route IDs, multiple if waypoints are set",
    )

    # Productivity and Communication State
    email_addresses_sent_mail_to: list[str] = Field(
        default=[], description="All email adresses where a mail was sent to"
    )
    phone_numbers_called: list[str] = Field(
        default=[], description="All phone numbers that were called"
    )

    # Charging State
    # remaining_range: int = Field(default=200, ge=0, le=500, description="Remaining range in km")

    # User Interaction
    # user_confirmation: list[dict[str, bool]] = Field(default_factory=list, description="User confirmation status for each confirmation request")

    # class Config:
    #     validate_assignment = True
    model_config = ConfigDict(validate_assignment=True)

    def __init__(self, **data):
        super().__init__(**data)
        self._lock = threading.Lock()

    def update_state(self, **kwargs):
        with self._lock:
            for key, value in kwargs.items():
                if not hasattr(self, key):
                    continue
                setattr(self, key, value)
                if key == "waypoints_id":
                    from dataset_domains.CarBench.context.fixed_context import (
                        fixed_context,
                    )

                    fixed_ctx = fixed_context.get()
                    if value:
                        if value[0] != fixed_ctx.current_location.id:
                            policy_errors_during_runtime.get().append(
                                f"TECH-AUT-POL:016:The start of the overall route set always has to be the current car location."
                            )


def check_waypoints_valid(value: List) -> bool:
    from dataset_domains.CarBench.context.fixed_context import (
        fixed_context,
    )

    fixed_ctx = fixed_context.get()
    if not value:
        return True
    if value[0] != fixed_ctx.current_location.id:
        return False
    return True
