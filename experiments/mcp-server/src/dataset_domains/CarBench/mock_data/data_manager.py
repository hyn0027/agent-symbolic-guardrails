import json
import math
import os
import threading
import time
from typing import Any, Dict, List, Optional


def read_jsonl_file(file_path: str):
    """Generator to yield parsed JSON objects from a JSONL file line by line."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        pass
                        # print(
                        #     f"Warning: Skipping invalid JSON line in {os.path.basename(file_path)}: {line[:100]}..."
                        # )
    except FileNotFoundError:
        # Modify to just return an empty iterator instead of printing error directly?
        # This allows the calling function to handle "file not found" more gracefully if needed.
        pass
        # print(f"Warning: File not found at {file_path}. Returning empty iterator.")
        # Or keep the print and return empty:
        # print(f"Error: File not found at {file_path}")
        # yield from () # Returns an empty generator
    except Exception as e:
        pass
        # print(f"Error reading file {file_path}: {e}")
        # yield from ()


# --- Thread-Safe DataManager ---


class DataManager:
    def __init__(self, base_data_path: str, preload: bool = False):
        """
        Initializes the thread-safe DataManager.

        Args:
            base_data_path: Path to the directory containing the 'navigation'
                            and 'productivity_and_communication' subfolders.
            preload: If True, load all data during initialization instead of lazy loading.
        """
        # Ensure base path exists or handle error?
        if not os.path.isdir(base_data_path):
            # Or raise an error depending on desired behavior
            pass
            # print(f"Warning: Base data path does not exist: {base_data_path}")

        self.nav_folder_path = os.path.join(base_data_path, "navigation")
        self.prod_comm_folder_path = os.path.join(
            base_data_path, "productivity_and_communication"
        )

        # --- Define File Paths ---
        self._locations_file = os.path.join(self.nav_folder_path, "locations.jsonl")
        self._pois_file = os.path.join(self.nav_folder_path, "pois.jsonl")
        self._weather_file = os.path.join(self.nav_folder_path, "weather.jsonl")
        self._routes_loc_loc_file = os.path.join(
            self.nav_folder_path, "routes_location_location.jsonl"
        )
        self._routes_loc_poi_file = os.path.join(
            self.nav_folder_path, "routes_location_poi.jsonl"
        )
        self._routes_poi_loc_file = os.path.join(
            self.nav_folder_path, "routes_poi_location.jsonl"
        )
        self._contacts_file = os.path.join(self.prod_comm_folder_path, "contacts.jsonl")
        self._calendars_file = os.path.join(
            self.prod_comm_folder_path, "calendars.jsonl"
        )
        self._routes_metadata_file = os.path.join(
            self.nav_folder_path, "routes_metadata.jsonl"
        )
        self._routes_index_file = os.path.join(
            self.nav_folder_path, "routes_index.jsonl"
        )

        # --- Caches (Loaded) ---
        self._locations_cache = None
        self._pois_cache = None
        self._weather_cache = None
        self._contacts_cache = None
        self._contacts_by_email = None
        self._contacts_by_phone = None
        self._routes_metadata_cache = None
        self._routes_by_id_cache = {}
        self._routes_by_pair_cache = {}
        self._route_type_map = {}

        # --- Threading Locks ---
        self._locations_lock = threading.Lock()
        self._pois_lock = threading.Lock()
        self._weather_lock = threading.Lock()
        self._contacts_lock = threading.Lock()
        self._routes_metadata_lock = threading.Lock()
        self._routes_lock = threading.Lock()
        self._route_type_map_lock = threading.Lock()

        # print(f"DataManager initialized. Navigation path: {self.nav_folder_path}")

        # Preload all data if requested
        if preload:
            self._preload_all_data()

    # --- Loading Properties with Threading Locks ---
    # (Unchanged: locations, pois, weather, contacts properties and _load_contacts_cache)
    @property
    def locations(self) -> Dict[str, Dict[str, Any]]:
        if self._locations_cache is None:
            with self._locations_lock:
                if self._locations_cache is None:
                    # print(f"Thread {threading.get_ident()}: Loading locations cache...")
                    try:
                        self._locations_cache = {
                            loc["id"]: loc
                            for loc in read_jsonl_file(self._locations_file)
                            if "id" in loc
                        }
                    except Exception as e:
                        # print(f"ERROR loading locations cache: {e}")
                        self._locations_cache = {}
                    # print(
                    #     f"Thread {threading.get_ident()}: Loaded {len(self._locations_cache)} locations."
                    # )
        return self._locations_cache if self._locations_cache is not None else {}

    @property
    def pois(self) -> Dict[str, Dict[str, Any]]:
        if self._pois_cache is None:
            with self._pois_lock:
                if self._pois_cache is None:
                    # print(f"Thread {threading.get_ident()}: Loading POIs cache...")
                    try:
                        self._pois_cache = {
                            poi["id"]: poi
                            for poi in read_jsonl_file(self._pois_file)
                            if "id" in poi
                        }
                    except Exception as e:
                        # print(f"ERROR loading POIs cache: {e}")
                        self._pois_cache = {}
                    # print(
                    #     f"Thread {threading.get_ident()}: Loaded {len(self._pois_cache)} POIs."
                    # )
        return self._pois_cache if self._pois_cache is not None else {}

    @property
    def weather(self) -> Dict[str, Dict[str, Any]]:
        if self._weather_cache is None:
            with self._weather_lock:
                if self._weather_cache is None:
                    # print(f"Thread {threading.get_ident()}: Loading weather cache...")
                    try:
                        self._weather_cache = {
                            w["location_id"]: w
                            for w in read_jsonl_file(self._weather_file)
                            if "location_id" in w
                        }
                    except Exception as e:
                        # print(f"ERROR loading weather cache: {e}")
                        self._weather_cache = {}
                    # print(
                    #     f"Thread {threading.get_ident()}: Loaded {len(self._weather_cache)} weather entries."
                    # )
        return self._weather_cache if self._weather_cache is not None else {}

    @property
    def contacts(self) -> Dict[str, Dict[str, Any]]:
        if self._contacts_cache is None:
            with self._contacts_lock:
                if self._contacts_cache is None:
                    # print(
                    #     f"Thread {threading.get_ident()}: Triggering load for contacts cache..."
                    # )
                    self._load_contacts_cache()
        return self._contacts_cache if self._contacts_cache is not None else {}

    def _preload_all_data(self):
        """Preloads all data into memory for faster access."""
        # print("Preloading all data...")
        start_time = time.time()

        # Access all properties to trigger their loading
        _ = self.locations
        _ = self.pois
        _ = self.weather
        _ = self.contacts
        _ = self.routes_metadata

        # Load route indices
        self._load_route_indices()

        # Preload some common routes into cache
        preloaded_routes = 0
        max_preload = 3000000  # Limit to avoid excessive memory usage

        try:
            # Load some location-to-location routes
            for data in read_jsonl_file(self._routes_loc_loc_file):
                if preloaded_routes >= max_preload:
                    break

                route_id = data.get("route_id")
                if route_id:
                    with self._routes_lock:
                        self._routes_by_id_cache[route_id] = data
                    preloaded_routes += 1
        except Exception as e:
            pass
            # print(f"Warning: Error preloading location-location routes: {e}")

        elapsed = time.time() - start_time
        # print(
        #     f"Preloading complete. Loaded {len(self.locations)} locations, {len(self.pois)} POIs, "
        #     f"{len(self.weather)} weather entries, {len(self.contacts)} contacts, "
        #     f"{len(self.routes_metadata)} route metadata entries, and {preloaded_routes} routes. "
        #     f"Time: {elapsed:.2f} seconds"
        # )

    def _load_contacts_cache(self):
        # print(f"Thread {threading.get_ident()}: Loading contacts cache...")
        temp_contacts_cache, temp_contacts_by_email, temp_contacts_by_phone = {}, {}, {}
        try:
            for contact in read_jsonl_file(self._contacts_file):
                contact_id, email, phone = (
                    contact.get("id"),
                    contact.get("email"),
                    contact.get("phone_number"),
                )
                if contact_id:
                    temp_contacts_cache[contact_id] = contact
                if email:
                    temp_contacts_by_email[email] = contact
                if phone:
                    temp_contacts_by_phone[phone] = contact
            self._contacts_cache, self._contacts_by_email, self._contacts_by_phone = (
                temp_contacts_cache,
                temp_contacts_by_email,
                temp_contacts_by_phone,
            )
            # print(
            #     f"Thread {threading.get_ident()}: Loaded {len(self._contacts_cache)} contacts."
            # )

        except Exception as e:
            # print(f"ERROR loading contacts cache: {e}")
            self._contacts_cache, self._contacts_by_email, self._contacts_by_phone = (
                {},
                {},
                {},
            )

    @property
    def routes_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Loading property for route metadata."""
        if self._routes_metadata_cache is None:
            with self._routes_metadata_lock:
                if self._routes_metadata_cache is None:
                    # print(
                    #     f"Thread {threading.get_ident()}: Loading routes metadata cache..."
                    # )
                    try:
                        self._routes_metadata_cache = {
                            route_meta["route_id"]: route_meta
                            for route_meta in read_jsonl_file(
                                self._routes_metadata_file
                            )
                            if "route_id" in route_meta
                        }
                    except Exception as e:
                        # print(f"ERROR loading routes metadata cache: {e}")
                        self._routes_metadata_cache = {}
                    # print(
                    # f"Thread {threading.get_ident()}: Loaded {len(self._routes_metadata_cache)} route metadata entries."
                    # )
        return (
            self._routes_metadata_cache
            if self._routes_metadata_cache is not None
            else {}
        )

    def _generate_route_from_metadata(
        self, route_metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Dynamically generates a route based on metadata."""
        route_id = route_metadata.get("route_id")
        start_id = route_metadata.get("start_id")
        dest_id = route_metadata.get("destination_id")
        base_route_id = route_metadata.get("base_route_id")

        # If no base route ID, we can't generate the route
        if not base_route_id:
            return None

        # Get the base route
        base_route = self.get_route_by_id(base_route_id)
        if not base_route:
            return None

        # Handle POIs along routes or route to POI via corresponding location
        fraction = route_metadata.get("fraction")
        detour_distance_km = route_metadata.get("detour_distance_km", 0)
        is_reverse = route_metadata.get("is_reverse", False)

        # Base values from the base route
        base_distance = base_route.get("distance_km", 0)
        base_duration_h = base_route.get("duration_hours", 0)
        base_duration_m = base_route.get("duration_minutes", 0)
        base_road_types = base_route.get("road_types", ["country road"])
        base_name_via = base_route.get("name_via", "")
        base_includes_toll = base_route.get("includes_toll", False)
        base_alias = base_route.get("alias", [])

        # Create the new route based on base route + metadata
        if fraction is not None:
            # This is a POI along a route
            # Calculate partial distance and duration based on fraction
            adjusted_distance = base_distance * fraction

            # Convert base duration to minutes
            base_duration_total_min = (base_duration_h * 60) + base_duration_m
            adjusted_duration_min = base_duration_total_min * fraction

            # Add detour
            total_distance = adjusted_distance + detour_distance_km

            # Calculate duration for detour (assuming 50 km/h average)
            detour_duration_min = (detour_distance_km / 50.0) * 60
            total_duration_min = adjusted_duration_min + detour_duration_min

            # Convert back to hours and minutes
            adjusted_duration_h = int(total_duration_min // 60)
            adjusted_duration_m = math.ceil(total_duration_min % 60)
        else:
            # This is a POI accessed via its corresponding location
            # Just add detour to base route
            total_distance = base_distance + detour_distance_km

            # Calculate duration for detour (assuming 50 km/h average)
            detour_duration_min = (detour_distance_km / 50.0) * 60
            base_duration_total_min = (base_duration_h * 60) + base_duration_m
            total_duration_min = base_duration_total_min + detour_duration_min

            # Convert back to hours and minutes
            adjusted_duration_h = int(total_duration_min // 60)
            adjusted_duration_m = math.ceil(total_duration_min % 60)

        # Handle route aliases based on alternative index
        route_alt_idx = route_metadata.get("route_alternative", 0)
        if not base_alias:
            base_alias = []
            if route_alt_idx == 0:
                base_alias.extend(["fastest", "first"])
            elif route_alt_idx == 1:
                base_alias.append("second")
            elif route_alt_idx == 2:
                base_alias.append("third")

        # Create the route object
        return {
            "route_id": route_id,
            "start_id": start_id,
            "destination_id": dest_id,
            "name_via": base_name_via,
            "distance_km": round(total_distance, 2),
            "duration_hours": adjusted_duration_h,
            "duration_minutes": adjusted_duration_m,
            "road_types": base_road_types,
            "includes_toll": base_includes_toll,
            "alias": base_alias,
            "base_route_id": base_route_id,
        }

    # --- Search Methods (Leveraging Cache or File Reading) ---
    # (Unchanged: get_location_by_id, get_poi_by_id, get_weather_for_location,
    #  get_weather_for_point, get_pois_for_location)
    def get_location_by_id(self, location_id: str) -> Optional[Dict[str, Any]]:
        return self.locations.get(location_id)

    def get_poi_by_id(self, poi_id: str) -> Optional[Dict[str, Any]]:
        return self.pois.get(poi_id)

    def get_weather_for_location(self, location_id: str) -> Optional[Dict[str, Any]]:
        return self.weather.get(location_id)

    def get_weather_for_point(self, point_id: str) -> Optional[Dict[str, Any]]:
        target_location_id = None
        if point_id.startswith("loc_"):
            target_location_id = point_id if self.get_location_by_id(point_id) else None
        elif point_id.startswith("poi_"):
            poi_data = self.get_poi_by_id(point_id)
            target_location_id = (
                poi_data.get("corresponding_location_id") if poi_data else None
            )
        return (
            self.get_weather_for_location(target_location_id)
            if target_location_id
            else None
        )

    def get_pois_for_location(self, location_id: str) -> List[Dict[str, Any]]:
        return [
            poi
            for poi in self.pois.values()
            if poi.get("corresponding_location_id") == location_id
        ]

    # --- Methods Reading Route Files (No Cache) ---

    def get_routes_location_to_location(
        self, start_loc_id: str, dest_loc_id: str
    ) -> List[Dict[str, Any]]:
        """Gets route alternatives between locations with optimized lookup."""
        # Check pair cache first
        pair_key = (start_loc_id, dest_loc_id)
        route_ids = []

        # Load route indices if needed
        if not self._routes_by_pair_cache:
            self._load_route_indices()

        with self._routes_lock:
            route_ids = self._routes_by_pair_cache.get(pair_key, [])

        # If we have route IDs, retrieve each route
        routes = []
        for route_id in route_ids:
            route = self.get_route_by_id(route_id)
            if route:
                routes.append(route)

        return routes

    def get_routes_location_to_poi(
        self, start_loc_id: str, dest_poi_id: str
    ) -> List[Dict[str, Any]]:
        """Gets routes from location to POI with optimized lookup."""
        # Check pair cache first
        pair_key = (start_loc_id, dest_poi_id)
        route_ids = []

        # Load route indices if needed
        if not self._routes_by_pair_cache:
            self._load_route_indices()

        with self._routes_lock:
            route_ids = self._routes_by_pair_cache.get(pair_key, [])

        # If we have route IDs, retrieve each route
        routes = []
        for route_id in route_ids:
            route = self.get_route_by_id(route_id)
            if route:
                routes.append(route)

        return routes

    # ***** ADDED METHOD *****
    def get_routes_poi_to_location(
        self, start_poi_id: str, dest_loc_id: str
    ) -> List[Dict[str, Any]]:
        """Gets routes from POI to location with optimized lookup."""
        # Check pair cache first
        pair_key = (start_poi_id, dest_loc_id)
        route_ids = []

        # Load route indices if needed
        if not self._routes_by_pair_cache:
            self._load_route_indices()

        with self._routes_lock:
            route_ids = self._routes_by_pair_cache.get(pair_key, [])

        # If we have route IDs, retrieve each route
        routes = []
        for route_id in route_ids:
            route = self.get_route_by_id(route_id)
            if route:
                routes.append(route)

        return routes

    # ************************

    def get_route_by_id(self, route_id: str) -> Optional[Dict[str, Any]]:
        """Gets a route by ID with optimized lookup."""
        # Check cache first
        with self._routes_lock:
            if route_id in self._routes_by_id_cache:
                return self._routes_by_id_cache[route_id]

        # Load route type map if not loaded
        if not self._route_type_map:
            self._load_route_indices()

        # Determine which file to look in (or if dynamic generation needed)
        route_type = self._route_type_map.get(route_id)
        if not route_type:
            return None

        route_data = None

        # Based on type, look in appropriate file or generate
        if route_type == "loc-loc":
            for data in read_jsonl_file(self._routes_loc_loc_file):
                if data.get("route_id") == route_id:
                    route_data = data
                    break
        elif route_type == "loc-poi":
            for data in read_jsonl_file(self._routes_loc_poi_file):
                if data.get("route_id") == route_id:
                    route_data = data
                    break
        elif route_type == "poi-loc":
            for data in read_jsonl_file(self._routes_poi_loc_file):
                if data.get("route_id") == route_id:
                    route_data = data
                    break
        elif route_type == "metadata":
            # Dynamic generation needed
            metadata = self.routes_metadata.get(route_id)
            if metadata:
                route_data = self._generate_route_from_metadata(metadata)

        # Cache result before returning
        if route_data:
            with self._routes_lock:
                self._routes_by_id_cache[route_id] = route_data

        return route_data

    # --- Productivity/Communication Methods (Unchanged) ---
    def get_calendar_line(self, calendar_id: str) -> Optional[Dict[str, Any]]:
        for data in read_jsonl_file(self._calendars_file):
            if data.get("id") == calendar_id:
                return data
        return None

    def load_all_contacts(self) -> List[Dict[str, Any]]:
        return list(self.contacts.values())

    def get_contact_information(self, contact_id: str) -> Optional[Dict[str, Any]]:
        return self.contacts.get(contact_id)

    def check_if_email_in_contacts(self, email: str) -> bool:
        if self._contacts_by_email is None:
            _ = self.contacts
        return email in (self._contacts_by_email or {})

    def check_if_phone_number_in_contacts(self, phone_number: str) -> bool:
        if self._contacts_by_phone is None:
            _ = self.contacts
        return phone_number in (self._contacts_by_phone or {})

    # Add this method for loading route indices
    def _load_route_indices(self):
        """Loads route indices for fast lookup from the pre-computed index file."""
        # print(f"Thread {threading.get_ident()}: Loading route indices...")

        route_type_map = {}
        routes_by_pair = {}

        try:
            for entry in read_jsonl_file(self._routes_index_file):
                route_id = entry.get("route_id")
                start_id = entry.get("start_id")
                dest_id = entry.get("destination_id")
                route_type = entry.get("type")

                if route_id and start_id and dest_id and route_type:
                    route_type_map[route_id] = route_type
                    pair_key = (start_id, dest_id)
                    if pair_key not in routes_by_pair:
                        routes_by_pair[pair_key] = []
                    routes_by_pair[pair_key].append(route_id)

            with self._route_type_map_lock:
                self._route_type_map = route_type_map

            with self._routes_lock:
                self._routes_by_pair_cache = routes_by_pair

            # print(
            # f"Thread {threading.get_ident()}: Loaded indices for {len(route_type_map)} routes "
            # f"across {len(routes_by_pair)} unique route pairs."
            # )

        except Exception as e:
            # print(f"Warning: Error loading route indices: {e}")
            # Fallback to scanning files
            self._build_route_indices_from_files()

    # Fallback method if index file isn't available
    def _build_route_indices_from_files(self):
        """Builds route indices by scanning all route files."""
        # print(f"Thread {threading.get_ident()}: Building route indices from files...")

        route_type_map = {}
        routes_by_pair = {}

        # Process loc-loc routes
        try:
            for route in read_jsonl_file(self._routes_loc_loc_file):
                route_id = route.get("route_id")
                start_id = route.get("start_id")
                dest_id = route.get("destination_id")

                if route_id and start_id and dest_id:
                    route_type_map[route_id] = "loc-loc"
                    pair_key = (start_id, dest_id)
                    if pair_key not in routes_by_pair:
                        routes_by_pair[pair_key] = []
                    routes_by_pair[pair_key].append(route_id)
        except Exception as e:
            # print(f"Warning: Error indexing loc-loc routes: {e}")
            pass

        # Process loc-poi routes
        try:
            for route in read_jsonl_file(self._routes_loc_poi_file):
                route_id = route.get("route_id")
                start_id = route.get("start_id")
                dest_id = route.get("destination_id")

                if route_id and start_id and dest_id:
                    route_type_map[route_id] = "loc-poi"
                    pair_key = (start_id, dest_id)
                    if pair_key not in routes_by_pair:
                        routes_by_pair[pair_key] = []
                    routes_by_pair[pair_key].append(route_id)
        except Exception as e:
            # print(f"Warning: Error indexing loc-poi routes: {e}")
            pass

        # Process poi-loc routes
        try:
            for route in read_jsonl_file(self._routes_poi_loc_file):
                route_id = route.get("route_id")
                start_id = route.get("start_id")
                dest_id = route.get("destination_id")

                if route_id and start_id and dest_id:
                    route_type_map[route_id] = "poi-loc"
                    pair_key = (start_id, dest_id)
                    if pair_key not in routes_by_pair:
                        routes_by_pair[pair_key] = []
                    routes_by_pair[pair_key].append(route_id)
        except Exception as e:
            # print(f"Warning: Error indexing poi-loc routes: {e}")
            pass

        # Process metadata
        try:
            for metadata in read_jsonl_file(self._routes_metadata_file):
                route_id = metadata.get("route_id")
                start_id = metadata.get("start_id")
                dest_id = metadata.get("destination_id")

                if route_id and start_id and dest_id:
                    route_type_map[route_id] = "metadata"
                    pair_key = (start_id, dest_id)
                    if pair_key not in routes_by_pair:
                        routes_by_pair[pair_key] = []
                    routes_by_pair[pair_key].append(route_id)
        except Exception as e:
            # print(f"Warning: Error indexing route metadata: {e}")
            pass

        with self._route_type_map_lock:
            self._route_type_map = route_type_map

        with self._routes_lock:
            self._routes_by_pair_cache = routes_by_pair

        # print(
        # f"Thread {threading.get_ident()}: Built indices for {len(route_type_map)} routes "
        # f"across {len(routes_by_pair)} unique route pairs."
        # )


def main():
    """
    Main function for testing DataManager functionality.
    Set a breakpoint at the 'pass' statement below to manually test functions.
    """
    # Initialize DataManager
    base_data_path = os.path.join(os.path.dirname(__file__))
    dm = DataManager(base_data_path, preload=True)

    # print("\n=== DataManager Testing Examples ===")
    # print(
    # "Set a breakpoint at the 'pass' statement and use these examples in the debug console:\n"
    # )

    # Property access examples
    # print("# Property access examples:")
    # print("locations = dm.locations")
    # print("pois = dm.pois")
    # print("weather = dm.weather")
    # print("contacts = dm.contacts")
    # print("routes_metadata = dm.routes_metadata")
    # print()

    # Location methods examples
    # print("# Location methods examples:")
    # print("location = dm.get_location_by_id('loc_berlin')")
    # print("location = dm.get_location_by_id('loc_munich')")
    # print("location = dm.get_location_by_id('loc_hamburg')")
    # print()

    # POI methods examples
    # print("# POI methods examples:")
    # print("poi = dm.get_poi_by_id('poi_restaurant_berlin_001')")
    # print("poi = dm.get_poi_by_id('poi_hotel_munich_001')")
    # print("pois_for_location = dm.get_pois_for_location('loc_berlin')")
    # print("pois_for_location = dm.get_pois_for_location('loc_munich')")
    # print()

    # Weather methods examples
    # print("# Weather methods examples:")
    # print("weather = dm.get_weather_for_location('loc_berlin')")
    # print("weather = dm.get_weather_for_point('loc_munich')")
    # print("weather = dm.get_weather_for_point('poi_restaurant_berlin_001')")
    # print()

    # Route methods examples
    # print("# Route methods examples:")
    # print("routes = dm.get_routes_location_to_location('loc_berlin', 'loc_munich')")
    # print("routes = dm.get_routes_location_to_location('loc_hamburg', 'loc_berlin')")
    # print(
    # "routes = dm.get_routes_location_to_poi('loc_berlin', 'poi_restaurant_munich_001')"
    # )
    # print(
    # "routes = dm.get_routes_poi_to_location('poi_hotel_berlin_001', 'loc_munich')"
    # )
    # print("route = dm.get_route_by_id('route_berlin_munich_001')")
    # print()

    # Contact methods examples
    # print("# Contact methods examples:")
    # print("all_contacts = dm.load_all_contacts()")
    # print("contact = dm.get_contact_information('contact_001')")
    # print("has_email = dm.check_if_email_in_contacts('john.doe@example.com')")
    # print("has_phone = dm.check_if_phone_number_in_contacts('+49123456789')")
    # print()

    # Calendar methods examples
    # print("# Calendar methods examples:")
    # print("calendar = dm.get_calendar_line('calendar_001')")
    # print()

    # print("\n=== Set breakpoint here for manual testing ===")
    # Set your breakpoint on the next line
    pass  # <-- Set breakpoint here and use the debug console to test functions


if __name__ == "__main__":
    main()
