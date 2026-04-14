from .charging.get_apis.calculate_charging_soc_by_time import CalculateChargingSocByTime
from .charging.get_apis.calculate_charging_time_by_soc import CalculateChargingTimeBySoc
from .charging.get_apis.get_charging_status import GetChargingStatus
from .charging.get_apis.get_distance_by_soc import GetDistanceBySoc
from .cross_domain.calculate_datetime import CalculateDateTime
from .cross_domain.calculate_math import CalculateMath
from .cross_domain.planning import PlanningTool
from .cross_domain.think import Think
from .navigation.get_apis.convert_route_distance_and_time import (
    ConvertRouteDistanceIntoTime,
)
from .navigation.get_apis.get_current_navigation_state import GetCurrentNavigationState
from .navigation.get_apis.get_location_id_by_location_name import (
    GetLocationIdByLocationName,
)
from .navigation.get_apis.get_routes_from_start_to_destination import GetRoutes
from .navigation.get_apis.search_poi_along_the_route import SearchPoiAlongTheRoute
from .navigation.get_apis.search_poi_at_location import SearchPoiAtLocation
from .navigation.set_apis.delete_current_navigation import DeleteCurrentNavigation
from .navigation.set_apis.navigation_add_one_waypoint import NavigationAddOneWaypoint
from .navigation.set_apis.navigation_delete_final_destination import (
    NavigationDeleteFinalDestination,
)
from .navigation.set_apis.navigation_delete_one_waypoint import (
    NavigationDeleteOneWaypoint,
)
from .navigation.set_apis.navigation_replace_final_destination import (
    NavigationReplaceFinalDestination,
)
from .navigation.set_apis.navigation_replace_one_waypoint import (
    NavigationReplaceOneWaypoint,
)
from .navigation.set_apis.set_new_navigation import SetNewNavigation
from .preferences.get_user_preferences import GetUserPreferences
from .productivity_and_communication.get_apis.get_contact_id_by_contact_name import (
    GetContactIdByContactName,
)
from .productivity_and_communication.get_apis.get_contact_information import (
    GetContactInformation,
)
from .productivity_and_communication.get_apis.get_entries_from_calendar import (
    GetEntriesFromCalendar,
)
from .productivity_and_communication.set_apis.call_phone_by_number import (
    CallPhoneByNumber,
)
from .productivity_and_communication.set_apis.send_email import SendEmail
from .vehicle_functions.get_apis.get_ambient_light_status_and_color import (
    GetAmbientLightStatusAndColor,
)
from .vehicle_functions.get_apis.get_car_color import GetCarColor
from .vehicle_functions.get_apis.get_climate_settings import GetClimateSettings
from .vehicle_functions.get_apis.get_exterior_lights_status import (
    GetExteriorLightsStatus,
)
from .vehicle_functions.get_apis.get_fuel_information import GetFuelInformation
from .vehicle_functions.get_apis.get_reading_lights_status import GetReadingLightsStatus
from .vehicle_functions.get_apis.get_seat_heating_level import GetSeatHeatingLevel
from .vehicle_functions.get_apis.get_seats_occupancy import GetSeatsOccupancy
from .vehicle_functions.get_apis.get_steering_wheel_heating_level import (
    GetSteeringWheelHeatingLevel,
)
from .vehicle_functions.get_apis.get_sunroof_and_sunshade_position import (
    GetSunroofAndSunshadePosition,
)
from .vehicle_functions.get_apis.get_temperature_inside_car import (
    GetTemperatureInsideCar,
)
from .vehicle_functions.get_apis.get_trunk_door_position import GetTrunkDoorPosition
from .vehicle_functions.get_apis.get_window_positions import GetWindowPositions
from .vehicle_functions.set_apis.open_close_sunroof import OpenCloseSunroof
from .vehicle_functions.set_apis.open_close_sunshade import OpenCloseSunshade
from .vehicle_functions.set_apis.open_close_trunk_door import OpenCloseTrunkDoor
from .vehicle_functions.set_apis.open_close_window import OpenCloseWindow
from .vehicle_functions.set_apis.set_air_circulation import SetAirCirculation
from .vehicle_functions.set_apis.set_air_conditioning import SetAirConditioning
from .vehicle_functions.set_apis.set_ambient_lights import SetAmbientLights
from .vehicle_functions.set_apis.set_climate_temperature import SetClimateTemperature
from .vehicle_functions.set_apis.set_fan_airflow_direction import SetFanAirflowDirection
from .vehicle_functions.set_apis.set_fan_speed import SetFanSpeed
from .vehicle_functions.set_apis.set_fog_lights import SetFogLights
from .vehicle_functions.set_apis.set_head_lights_high_beams import (
    SetHeadLightsHighBeams,
)
from .vehicle_functions.set_apis.set_head_lights_low_beams import SetHeadLightsLowBeams
from .vehicle_functions.set_apis.set_reading_light import SetReadingLight
from .vehicle_functions.set_apis.set_seat_heating import SetSeatHeating
from .vehicle_functions.set_apis.set_steering_wheel_heating import (
    SetSteeringWheelHeating,
)
from .vehicle_functions.set_apis.set_window_defrost import SetWindowDefrost
from .weather.get_apis.get_weather import GetWeather

SET_VEHICLE_STATE_TOOLS = [
    OpenCloseSunroof,
    OpenCloseSunshade,
    OpenCloseTrunkDoor,
    OpenCloseWindow,
    SetAirCirculation,
    SetAirConditioning,
    SetAmbientLights,
    SetClimateTemperature,
    SetFanAirflowDirection,
    SetFanSpeed,
    SetFogLights,
    SetHeadLightsHighBeams,
    SetHeadLightsLowBeams,
    SetReadingLight,
    SetSeatHeating,
    SetSteeringWheelHeating,
    SetWindowDefrost,
]

GET_VEHICLE_STATE_TOOLS = [
    GetAmbientLightStatusAndColor,
    GetCarColor,
    GetClimateSettings,
    GetExteriorLightsStatus,
    # GetFuelInformation,
    GetReadingLightsStatus,
    GetSeatHeatingLevel,
    GetSeatsOccupancy,
    GetSteeringWheelHeatingLevel,
    GetSunroofAndSunshadePosition,
    GetTemperatureInsideCar,
    GetTrunkDoorPosition,
    GetWindowPositions,
]

GET_WEATHER_TOOLS = [GetWeather]

GET_NAVIGATION_TOOLS = [
    SearchPoiAtLocation,
    SearchPoiAlongTheRoute,
    GetRoutes,
    GetLocationIdByLocationName,
    GetCurrentNavigationState,
    ConvertRouteDistanceIntoTime,
]

SET_NAVIGATION_TOOLS = [
    SetNewNavigation,
    NavigationAddOneWaypoint,
    NavigationReplaceOneWaypoint,
    NavigationReplaceFinalDestination,
    NavigationDeleteOneWaypoint,
    NavigationDeleteFinalDestination,
    DeleteCurrentNavigation,
]

GET_CHARGING_TOOLS = [
    GetChargingStatus,
    GetDistanceBySoc,
    CalculateChargingTimeBySoc,
    CalculateChargingSocByTime,
]

CROSS_DOMAIN_TOOLS = [CalculateMath, CalculateDateTime, Think, PlanningTool]

GET_PRODUCTIVITY_AND_COMMUNICATION_TOOLS = [
    GetContactIdByContactName,
    GetEntriesFromCalendar,
    GetContactInformation,
]

SET_PRODUCTIVITY_AND_COMMUNICATION_TOOLS = [CallPhoneByNumber, SendEmail]

GET_USER_PREFERENCES_TOOLS = [GetUserPreferences]

# join all tools
ALL_TOOLS = (
    GET_USER_PREFERENCES_TOOLS
    + CROSS_DOMAIN_TOOLS
    + SET_VEHICLE_STATE_TOOLS
    + GET_VEHICLE_STATE_TOOLS
    + GET_WEATHER_TOOLS
    + GET_NAVIGATION_TOOLS
    + SET_NAVIGATION_TOOLS
    + GET_CHARGING_TOOLS
    + GET_PRODUCTIVITY_AND_COMMUNICATION_TOOLS
    + SET_PRODUCTIVITY_AND_COMMUNICATION_TOOLS
)


for tool in ALL_TOOLS:
    tool.register_tool()

from .evaluator import *
from dataset_domains.CarBench.context.dynamic_context_state import (
    context_state,
)
from dataset_domains.CarBench.context.fixed_context import fixed_context


@mcp.tool(
    meta={
        "disclose_to_model": False,
    }
)
def get_user_confirmation_details(func_name, func_args: Dict[str, Any]) -> str:
    """
    Get details for user confirmation. For test only.
    """
    vehicle_ctx = context_state.get()
    fixed_ctx = fixed_context.get()
    if func_name == "open_close_window":  # LLM-POL:007
        percentage = func_args.get("percentage")
        ac = vehicle_ctx.air_conditioning
        if percentage > 25 and ac:
            return f"Warning: You are about to open the window more than 25% while the AC is ON, which may lead to energy inefficiency."
        return f"You are about to open the window to {percentage}%. Air conditioning is currently {'ON' if ac else 'OFF'}."
    if func_name == "open_close_sunroof":  # LLM-POL:008, AUT-POL:009
        percentage = func_args.get("percentage")
        weather = GetWeather.invoke(
            location_or_poi_id=fixed_ctx.current_location.id,
            month=fixed_ctx.current_datetime.month,
            day=fixed_ctx.current_datetime.day,
            time_hour_24hformat=fixed_ctx.current_datetime.hour,
            time_minutes=fixed_ctx.current_datetime.minute,
        )
        weather = json.loads(weather) if isinstance(weather, str) else weather
        allowed_conditions = ["sunny", "cloudy", "partly_cloudy"]
        if weather["status"] == "SUCCESS":
            current_weather = weather["result"]["current_slot"]["condition"]
            if percentage > 0 and current_weather not in allowed_conditions:
                return f"Warning: You are about to open the sunroof to {percentage}%, but the current weather condition is {current_weather}, which may not be suitable for opening the sunroof."
            elif percentage > 0:
                return f"You are about to open the sunroof to {percentage}%. The current weather condition is {current_weather}."
        elif percentage > 0:
            return f"Warning: You are about to open the sunroof to {percentage}%, but the weather information cannot be retrieved at the moment. Please proceed with caution."
    if func_name == "set_fog_lights":  # LLM-POL:008, AUT-POL:009
        on = func_args.get("on")
        weather = GetWeather.invoke(
            location_or_poi_id=fixed_ctx.current_location.id,
            month=fixed_ctx.current_datetime.month,
            day=fixed_ctx.current_datetime.day,
            time_hour_24hformat=fixed_ctx.current_datetime.hour,
            time_minutes=fixed_ctx.current_datetime.minute,
        )
        weather = json.loads(weather) if isinstance(weather, str) else weather
        allowed_conditions = ["cloudy_and_thunderstorm", "cloudy_and_hail"]
        if weather["status"] == "SUCCESS":
            current_weather = weather["result"]["current_slot"]["condition"]
            if on and current_weather not in allowed_conditions:
                return f"Warning: You are about to turn on the fog lights, but the current weather condition is {current_weather}, which may not be suitable for turning on the fog lights."
            elif on:
                return f"You are about to turn on the fog lights. The current weather condition is {current_weather}."
        elif on:
            return f"Warning: You are about to turn on the fog lights, but the weather information cannot be retrieved at the moment. Please proceed with caution."
    if func_name == "set_climate_temperature":
        temperature = func_args.get("temperature")
        seat_zone = func_args.get("seat_zone")
        if seat_zone == "DRIVER":
            current_passenger_temp = vehicle_ctx.climate_temperature_passenger
            diff = abs(temperature - current_passenger_temp)
            if diff > 3:
                return f"Warning: You are about to set the temperature to {temperature}°C for the DRIVER seat, which will result in a temperature difference of {diff}°C compared to the current passenger seat temperature. This may cause discomfort for the passenger."
        elif seat_zone == "PASSENGER":
            current_driver_temp = vehicle_ctx.climate_temperature_driver
            diff = abs(temperature - current_driver_temp)
            if diff > 3:
                return f"Warning: You are about to set the temperature to {temperature}°C for the PASSENGER seat, which will result in a temperature difference of {diff}°C compared to the current driver seat temperature. This may cause discomfort for the driver."
    if func_name == "get_routes_from_start_to_destination":
        return f"Warning: You are geting the fastest route. If you wants more information on alternative routes, please specify it in your request. Also, please be aware that the route may include toll roads, details can be find in the tool response details."
    if func_name == "get_current_navigation_state":
        return f"Warning: You are getting the current navigation state, which may include sensitive information such as the current location and destination. Please make sure to handle this information with care. The current route may include toll roads, details can be find in the tool response details."
    return ""
