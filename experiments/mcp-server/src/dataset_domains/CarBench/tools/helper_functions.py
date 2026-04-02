def check_correct_id_format(id: str, id_type: str) -> bool:
    """
    Check if the provided ID has the correct format.

    Parameters:
      id: The ID to check.
      id_type: The type of ID (e.g., "poi_or_location" or "route" or "contact" or "charging_plug").
    Returns:
      True if the ID has the correct format, False otherwise.
    """
    if id_type not in ["poi_or_location", "route", "contact", "charging_plug"]:
        raise ValueError("Invalid ID type.")

    if id_type == "poi_or_location":
        if (
            id[3] != "_"
            or id[7] != "_"
            or not id[8:].isdigit()
            or not (id[:3] == "poi" or id[:3] == "loc")
        ):
            return False
    elif id_type == "route":
        if (
            id[3] != "_"
            or id[7] != "_"
            or id[11] != "_"
            or not id[12:].isdigit()
            or not (
                id[:3] == "rll" or id[:3] == "rlp" or id[:3] == "rpl" or id[:3] == "rpp"
            )
        ):
            return False
    elif id_type == "contact":
        if id[3] != "_" or not id[4:].isdigit() or not id[:3] == "con":
            return False
    elif id_type == "charging_plug":
        if (
            id[3] != "_"
            or id[7] != "_"
            or not id[8:].isdigit()
            or not (id[:3] == "plg")
        ):
            return False
    return True
