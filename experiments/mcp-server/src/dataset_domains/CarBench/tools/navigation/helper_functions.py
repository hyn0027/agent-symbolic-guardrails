import datetime
import math
from typing import Any, Dict, List, Optional, Tuple

from dataset_domains.CarBench.context.fixed_context import fixed_context

# Earth's radius in meters
R = 6371000


def haversine(lon1, lat1, lon2, lat2):
    """
    Compute the great-circle angular distance (in radians) between two points
    given in degrees (lon, lat).
    """
    # Convert degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_point_projection_on_route(
    p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float]
) -> Tuple[Optional[float], Optional[float]]:
    """
    Calculates the cross-track and along-track distance of point p3 relative
    to the great-circle path from p1 to p2.

    Args:
        p1, p2: Tuples of (lon, lat) in degrees for start and end points.
        p3: Tuple of (lon, lat) in degrees for the point to project.

    Returns:
        Tuple[Optional[float], Optional[float]]:
            - Cross-track distance in meters (perpendicular distance to the path).
              Can be negative depending on side. Returns None if p1=p2.
            - Along-track distance in meters (distance from p1 along the path
              to the point of closest approach). Returns None if p1=p2.
              Value can be < 0 or > route distance if projection is outside segment.
    """
    try:
        delta13_rad = haversine(p1[0], p1[1], p3[0], p3[1])  # Angular distance p1 to p3
        delta12_rad = haversine(p1[0], p1[1], p2[0], p2[1])  # Angular distance p1 to p2

        # Handle case where start and end points are the same
        if (
            abs(delta12_rad) < 1e-9
        ):  # Use a small tolerance for floating point comparison
            # Cross-track is distance from p1 to p3, along-track is 0
            return delta13_rad * R, 0.0

        # Convert coordinates to radians for bearing calculations
        lon1, lat1 = map(math.radians, p1)
        lon2, lat2 = map(math.radians, p2)
        lon3, lat3 = map(math.radians, p3)

        # Initial bearings
        # Bearing from p1 to p3
        dlon_13 = lon3 - lon1
        y_13 = math.sin(dlon_13) * math.cos(lat3)
        x_13 = math.cos(lat1) * math.sin(lat3) - math.sin(lat1) * math.cos(
            lat3
        ) * math.cos(dlon_13)
        theta13_rad = math.atan2(y_13, x_13)

        # Bearing from p1 to p2
        dlon_12 = lon2 - lon1
        y_12 = math.sin(dlon_12) * math.cos(lat2)
        x_12 = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(
            lat2
        ) * math.cos(dlon_12)
        theta12_rad = math.atan2(y_12, x_12)

        # Cross-track angular distance (difference in bearings)
        # Use formula d_xt = asin(sin(d_13) * sin(θ_13 - θ_12)) * R
        # Ensure argument to asin is within [-1, 1] due to potential floating point inaccuracies
        sin_arg_xt = math.sin(delta13_rad) * math.sin(theta13_rad - theta12_rad)
        sin_arg_xt = max(-1.0, min(1.0, sin_arg_xt))
        delta_xt_rad = math.asin(sin_arg_xt)
        d_xt_meters = delta_xt_rad * R  # Signed cross-track distance

        # Along-track angular distance
        # Use formula d_at = acos(cos(d_13) / cos(d_xt)) * R
        # Need checks for potential division by zero or acos domain errors
        cos_delta_xt = math.cos(delta_xt_rad)
        if (
            abs(cos_delta_xt) < 1e-9
        ):  # Avoid division by near zero (point is very far off track)
            # Treat as if projection is at p1 if delta13 is small, otherwise unclear
            # For simplicity, let's return None or handle based on context
            # Returning along-track as 0 might be reasonable if d_xt is large?
            # Let's return 0 for now if point is 90 degrees off track.
            delta_at_rad = 0.0
        else:
            cos_arg_at = math.cos(delta13_rad) / cos_delta_xt
            # Clamp argument for acos due to potential floating point errors
            cos_arg_at = max(-1.0, min(1.0, cos_arg_at))
            delta_at_rad = math.acos(cos_arg_at)

        # Determine sign for along-track distance based on bearing difference
        # If the angle between bearings (p1->p2 and p1->p3) is > 90 degrees, projection is "behind" p1
        if abs(theta13_rad - theta12_rad) > (math.pi / 2):
            d_at_meters = -delta_at_rad * R  # Negative distance if behind p1
        else:
            d_at_meters = delta_at_rad * R

        return d_xt_meters, d_at_meters

    except ValueError:  # Catch potential math domain errors
        # print(
            # f"Warning: Math domain error during projection calculation for points {p1}, {p2}, {p3}"
        # )
        return None, None


def is_point_near_route(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    route_segment: Optional[List[float]] = None,
    threshold: float = 5000.0,
) -> Tuple[bool, Optional[float]]:
    """
    Check if point p3 (lon, lat in degrees) is within 'threshold' meters of
    the route segment between p1 and p2, and optionally within a specific
    kilometer range of the route.

    Args:
        p1, p2: Tuples of (lon, lat) in degrees representing start and end points.
        p3: Tuple of (lon, lat) in degrees for the point being checked.
        route_segment: Optional list [start_km, end_km] defining the segment.
        threshold: Max allowed perpendicular distance in meters.

    Returns:
        Tuple[bool, Optional[float]]:
            - bool: True if p3 is considered near the route segment, False otherwise.
            - Optional[float]: The along-track distance in kilometers from p1 where
                               p3 projects onto the route (or the closest endpoint),
                               if the point is near. None otherwise.
    """
    # Calculate total route distance
    delta12_rad = haversine(p1[0], p1[1], p2[0], p2[1])
    d12_meters = delta12_rad * R

    # Calculate cross-track and along-track distances
    d_xt_meters, d_at_meters_raw = get_point_projection_on_route(p1, p2, p3)

    if d_xt_meters is None or d_at_meters_raw is None:
        # Calculation failed or p1=p2 edge case needs specific handling maybe
        # If p1=p2, check distance p1 to p3 directly
        if abs(delta12_rad) < 1e-9:
            dist_p1_p3 = haversine(p1[0], p1[1], p3[0], p3[1]) * R
            if dist_p1_p3 <= threshold:
                # Check segment only if it starts at 0 for this case
                if route_segment is None or route_segment[0] == 0:
                    return True, 0.0
            return False, None  # Not near or outside segment
        else:
            # Projection calculation failed for some reason
            return False, None

    # Determine the distance to check against threshold and the effective along-track distance
    d_check_meters: float
    d_at_effective_meters: float

    if d_at_meters_raw < 0:  # Projection is before p1
        d_check_meters = haversine(p1[0], p1[1], p3[0], p3[1]) * R  # Distance to p1
        d_at_effective_meters = 0.0
    elif d_at_meters_raw > d12_meters:  # Projection is after p2
        d_check_meters = haversine(p2[0], p2[1], p3[0], p3[1]) * R  # Distance to p2
        d_at_effective_meters = d12_meters
    else:  # Projection is within the segment [p1, p2]
        d_check_meters = abs(d_xt_meters)  # Perpendicular distance
        d_at_effective_meters = d_at_meters_raw

    # 1. Check if the closest point on the segment is within the threshold distance
    if d_check_meters > threshold:
        return False, None  # Too far away

    # 2. Check if the projection falls within the specified route_segment (if any)
    if route_segment is not None:
        # Convert segment km to meters
        segment_start_meters = route_segment[0] * 1000.0
        segment_end_meters = route_segment[1] * 1000.0

        # Ensure segment bounds are valid relative to total route distance
        segment_start_meters = max(0.0, segment_start_meters)
        segment_end_meters = min(d12_meters, segment_end_meters)

        # Use a small tolerance for floating point comparisons
        tolerance = 1e-3  # 1 millimeter tolerance
        if (
            d_at_effective_meters < segment_start_meters - tolerance
            or d_at_effective_meters > segment_end_meters + tolerance
        ):
            return False, None  # Projection point is outside the specified segment

    # If both checks pass, the point is near
    # Return True and the effective along-track distance in kilometers
    d_at_km = d_at_effective_meters / 1000.0
    return True, round(d_at_km, 3)  # Round to e.g., 3 decimal places (meters)


def is_near_start_or_destination(p1, p2, p3, radius=2000):
    """
    Check if point p3 (lon, lat in degrees) is within 'radius' meters of either
    p1 or p2.

    Parameters:
      p1, p2, p3: Tuples of (lon, lat) in degrees.
      radius: Distance in meters.

    Returns:
      True if p3 is within the radius of p1 or p2, False otherwise.
    """
    d1 = haversine(p1[0], p1[1], p3[0], p3[1]) * R
    d2 = haversine(p2[0], p2[1], p3[0], p3[1]) * R
    return d1 <= radius or d2 <= radius


# Example usage:
if __name__ == "__main__":
    # Define points (lon, lat) in degrees.
    p1 = (11.57549, 48.13743)
    p2 = (11.661666273741911, 48.4359294412524)
    p3 = (11.633445668991625, 48.43663443786398)

    # print("Is p3 near the route (within 5000 m)?", is_point_near_route(p1, p2, p3))
    # print(
        # "Is p3 near start or destination (within 5000 m)?",
        # is_near_start_or_destination(p1, p2, p3, 5000),
    # )


def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes the Levenshtein distance between two strings."""
    len_s1, len_s2 = len(s1), len(s2)

    # Initialize matrix
    dp = [[0] * (len_s2 + 1) for _ in range(len_s1 + 1)]

    # Base cases
    for i in range(len_s1 + 1):
        dp[i][0] = i
    for j in range(len_s2 + 1):
        dp[0][j] = j

    # Compute distances
    for i in range(1, len_s1 + 1):
        for j in range(1, len_s2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # Deletion
                dp[i][j - 1] + 1,  # Insertion
                dp[i - 1][j - 1] + cost,  # Substitution
            )

    return dp[len_s1][len_s2]


def apply_filters(
    pois: List[Dict[str, Any]], filters: List[str]
) -> List[Dict[str, Any]]:
    """Apply the specified filters to the POIs list."""
    filtered_pois = []

    # check if valid filters are used
    valid_filters = [
        "any::currently_open",
        "charging_stations::has_available_plug",
        "charging_stations::has_dc_plug",
        "any::sort_by_distance",
    ]
    for filter_name in filters:
        if filter_name not in valid_filters:
            raise ValueError(
                f"Invalid filter: {filter_name}. Valid filters are: {valid_filters}"
            )
    for poi in pois:
        # Check if POI passes all filters
        if passes_all_filters(poi, filters):
            filtered_pois.append(poi)

    return filtered_pois


def passes_all_filters(poi: Dict[str, Any], filters: List[str]) -> bool:
    """Check if a POI passes all the specified filters."""
    for filter_name in filters:
        # Filter: any::currently_open
        if filter_name == "any::currently_open":
            if not is_currently_open(poi.get("opening_hours", "")):
                return False

        # Filter: charging_stations::has_available_plug
        elif filter_name == "charging_stations::has_available_plug":
            if poi.get("category") != "charging_stations":
                return False

            has_available_plug = False
            for plug in poi.get("charging_plugs", []):
                if plug.get("availability") == "available":
                    has_available_plug = True
                    break

            if not has_available_plug:
                return False

        # Filter: charging_stations::has_dc_plug
        elif filter_name == "charging_stations::has_dc_plug":
            if poi.get("category") != "charging_stations":
                return False

            has_dc_plug = False
            for plug in poi.get("charging_plugs", []):
                if plug.get("power_type") == "DC":
                    has_dc_plug = True
                    break

            if not has_dc_plug:
                return False

        # Skip "any::sort_by_distance" as it's handled separately in the sorting logic

    # All filters passed
    return True


def is_currently_open(opening_hours: str) -> bool:
    """
    Check if a POI is currently open based on its opening hours.
    Opening hours format example: "08:00h - 20:00h"
    """
    try:
        # Get current time
        fixed_ctx = fixed_context.get()
        now = datetime.time(
            hour=fixed_ctx.current_datetime.hour,
            minute=fixed_ctx.current_datetime.minute,
        )

        # Parse opening hours (format: "08:00h - 20:00h")
        if not opening_hours or opening_hours == "":
            return False

        parts = opening_hours.split(" - ")
        if len(parts) != 2:
            return False

        open_time_str = parts[0].replace("h", "")
        close_time_str = parts[1].replace("h", "")

        open_hour, open_minute = map(int, open_time_str.split(":"))
        close_hour, close_minute = map(int, close_time_str.split(":"))

        open_time = datetime.time(hour=open_hour, minute=open_minute)
        # Handle case where closing time is 24:00h (midnight)
        if close_hour == 24 and close_minute == 0:
            close_hour = 23
            close_minute = 59
        close_time = datetime.time(hour=close_hour, minute=close_minute)

        # Check if open 24 hours
        if (
            open_hour == 0
            and open_minute == 0
            and close_hour == 24
            and close_minute == 0
        ):
            return True

        # Handle crossing midnight case
        if close_time <= open_time:  # e.g., 22:00h - 06:00h
            return now >= open_time or now <= close_time
        else:
            return open_time <= now <= close_time

    except (ValueError, IndexError):
        # If there's any error parsing the time, assume it's closed
        # print(
            # f"Warning: Could not parse opening hours: '{opening_hours}'. Assuming closed."
        # )
        return False
