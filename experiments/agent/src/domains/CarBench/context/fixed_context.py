# car data (not settable by agent): state_of_charge, remaining_range, charging_curve, charging_speed_limit, battery capacity, average consumption per km, average consumption per hour, regen factor?, car_color, fuel_type (to delete), regular_fuel_consumption (to delete), remaining_fuel (to delete)

import contextvars
import threading
from typing import Dict, List, Literal

from pydantic import BaseModel, Field, ConfigDict

fixed_context: contextvars.ContextVar["FixedContext"] = contextvars.ContextVar(
    "fixed_context"
)


class LocationPosition(BaseModel):
    longitude: float
    latitude: float


class CurrentLocation(BaseModel):
    id: str
    name: str
    position: LocationPosition


class CurrenDateTime(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int


class PointsOfInterestPreferences(BaseModel):
    airports: List[str] = Field(default=[])
    bakery: List[str] = Field(default=[])
    fast_food: List[str] = Field(default=[])
    parking: List[str] = Field(default=[])
    public_toilets: List[str] = Field(default=[])
    restaurants: List[str] = Field(default=[])
    supermarkets: List[str] = Field(default=[])
    charging_stations: List[str] = Field(default=[])


class NavigationAndRoutingPreferences(BaseModel):
    route_selection: List[str] = Field(default=[])


class VehicleSettingsPreferences(BaseModel):
    climate_control: List[str] = Field(default=[])
    vehicle_settings: List[str] = Field(default=[])


class ProductivityAndCommunicationPreferences(BaseModel):
    email: List[str] = Field(default=[])
    calendar: List[str] = Field(default=[])


class WeatherPreferences(BaseModel):
    weather: List[str] = Field(default=[])


class UserPreferences(BaseModel):
    points_of_interest: PointsOfInterestPreferences = Field(
        default_factory=PointsOfInterestPreferences
    )
    navigation_and_routing: NavigationAndRoutingPreferences = Field(
        default_factory=NavigationAndRoutingPreferences
    )
    vehicle_settings: VehicleSettingsPreferences = Field(
        default_factory=VehicleSettingsPreferences
    )
    productivity_and_communication: ProductivityAndCommunicationPreferences = Field(
        default_factory=ProductivityAndCommunicationPreferences
    )
    weather: WeatherPreferences = Field(default_factory=WeatherPreferences)


class FixedContext(BaseModel):
    # --- Fixed Car Context
    car_color: str = Field(default="blue", description="Color of the car")
    # # gasoline
    # fuel_type: str = Field(default="gasoline", description="Type of fuel used by the car")
    # regular_fuel_consumption: float = Field(default=8, ge=0, le=20, description="Fuel consumption in liter per 100 km")
    # remaining_fuel: float = Field(default=50, ge=0, le=100, description="Remaining fuel in the tank")
    # electric
    battery_capacity_kwh: float = Field(
        default=80, ge=60, le=100, description="Total (brutto) battery capacity in kWh"
    )
    useable_battery_percentage: float = Field(
        default=95, ge=90, le=100, description="Percentage of battery that's usable"
    )
    max_charging_power_ac: Literal[11, 22] = Field(
        default=11, description="Maximum charging power in kW for AC charging"
    )
    max_charging_power_dc: Literal[150, 200, 250, 268, 300, 350, 1000] = Field(
        default=250, description="Maximum charging power in kW for DC charging"
    )
    energy_consumption: float = Field(
        default=15, ge=10, le=20, description="Power consumption in kWh/100km"
    )
    charging_curve_parameters: Dict[str, List[float]] = Field(
        default_factory=lambda: {
            "soc_tresholds": [5, 10, 20, 50, 70, 80, 90, 95, 100],
            "power_percentages": [60, 90, 100, 100, 100, 90, 70, 40, 20],
        },
        description="Charging curve parameters",
    )
    state_of_charge: float = Field(
        default=10, ge=10, le=100, description="State of charge of the battery"
    )

    # --- Fixed Environment Context ---
    seats_occupied: dict[str, bool] = Field(
        default_factory=lambda: {
            "driver": True,
            "passenger": False,
            "driver_rear": False,
            "passenger_rear": False,
        },
        description="Occupied seats",
    )
    current_location: CurrentLocation = Field(
        default_factory=lambda: CurrentLocation(
            id="loc_mun_9995",
            name="Munich",
            position=LocationPosition(longitude=11.575, latitude=48.1375),
        ),
        description="Current location",
    )
    current_datetime: CurrenDateTime = Field(
        default_factory=lambda: CurrenDateTime(
            year=2025, month=2, day=14, hour=12, minute=0
        ),
        description="Current date and time",
    )

    # --- Fixed User Preferences Context ---
    user_preferences: UserPreferences = Field(
        default_factory=UserPreferences,
        description="User preferences for various categories",
    )

    model_config = ConfigDict(validate_assignment=True)

    def __init__(self, **data):
        super().__init__(**data)
        self.__lock = threading.Lock()

    def update_state(self, **kwargs):
        with self.__lock:
            for key, value in kwargs.items():
                if not hasattr(self, key):
                    continue
                setattr(self, key, value)
