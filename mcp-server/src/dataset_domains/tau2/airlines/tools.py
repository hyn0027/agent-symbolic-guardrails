# Modified from TAU2 bench code

"""Toolkit for the airline reservation system."""

from datetime import datetime
from copy import deepcopy
from typing import List, Optional, Annotated, Tuple
from safety_check import process_error

from .data_model import (
    AirportCode,
    AirportInfo,
    CabinClass,
    Certificate,
    DirectFlight,
    Flight,
    FlightDateStatus,
    FlightDateStatusAvailable,
    FlightDateStatusLanded,
    FlightDateStatusCancelled,
    FlightDateStatusDelayed,
    FlightDataStatusFlying,
    FlightDB,
    FlightInfo,
    FlightType,
    Insurance,
    Passenger,
    Payment,
    Reservation,
    ReservationFlight,
    User,
    MembershipLevel,
    CancellationReason,
    CompensatonReason,
    db,
)
from .data_path import TMP_DB_PATH

from mcp_server import mcp
from config_loader import CONFIG

safeguard_config = CONFIG.SAFEGUARD


def _get_user(user_id: str) -> User:
    """Get user from database."""
    if user_id not in db.users:
        process_error(f"User {user_id} not found", ["implemented"])
    return db.users[user_id]


def _get_reservation(reservation_id: str) -> Reservation:
    """Get reservation from database."""
    if reservation_id not in db.reservations:
        process_error(f"Reservation {reservation_id} not found", ["implemented"])
    return db.reservations[reservation_id]


def _get_flight(flight_number: str) -> Flight:
    """Get flight from database."""
    if flight_number not in db.flights:
        process_error(f"Flight {flight_number} not found", ["implemented"])
    return db.flights[flight_number]


def _get_flight_instance(flight_number: str, date: str) -> FlightDateStatus:
    """Get flight instance from database."""
    flight = _get_flight(flight_number)
    if date not in flight.dates:
        process_error(
            f"Flight {flight_number} not found on date {date}", ["implemented"]
        )
    return flight.dates[date]


def _get_new_reservation_id() -> str:
    """Get a new reservation id.
    Assume each task makes at most 3 reservations

    Returns:
        A new reservation id.

    Raises:
        ValueError: If too many reservations are made.
    """
    for reservation_id in ["HATHAT", "HATHAU", "HATHAV"]:
        if reservation_id not in db.reservations:
            return reservation_id
    process_error("Too many reservations", ["implemented"])


def _get_new_payment_id() -> str:
    """Get a new payment id.
    Assume each task makes at most 3 payments

    Returns:
        A new payment id.
    """
    return [3221322, 3221323, 3221324]


def _get_datetime() -> str:
    """Get the current datetime."""
    return "2024-05-15T15:00:00"


def _search_direct_flight(
    date: str,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    leave_after: Optional[str] = None,
) -> list[DirectFlight]:
    """Search for direct flights

    Args:
        date: The date of the flight in the format 'YYYY-MM-DD', such as '2024-01-01'.
        origin: The origin city airport in three letters, such as 'JFK'.
        destination: The destination city airport in three letters, such as 'LAX'.
        leave_after: The time to leave after the flight, such as '15:00:00'.
    """
    results = []
    for flight in db.flights.values():
        check = (
            (origin is None or flight.origin == origin)
            and (destination is None or flight.destination == destination)
            and (date in flight.dates)
            and (flight.dates[date].status == "available")
            and (
                leave_after is None
                or flight.scheduled_departure_time_est >= leave_after
            )
        )
        if check:
            direct_flight = DirectFlight(
                flight_number=flight.flight_number,
                origin=flight.origin,
                destination=flight.destination,
                status="available",
                scheduled_departure_time_est=flight.scheduled_departure_time_est,
                scheduled_arrival_time_est=flight.scheduled_arrival_time_est,
                available_seats=flight.dates[date].available_seats,
                prices=flight.dates[date].prices,
            )
            results.append(direct_flight)
    return results


def _payment_for_update(
    user: User, payment_id: str, total_price: int
) -> Optional[Payment]:
    """
    Process payment for update reservation

    Args:
        user: The user to process payment for.
        payment_id: The payment id to process.
        total_price: The total price to process.
        reservation: The reservation to process payment for.

    Raises:
        ValueError: If the payment method is not found.
        ValueError: If the certificate is used to update reservation.
        ValueError: If the gift card balance is not enough.
    """
    # Check payment
    if payment_id not in user.payment_methods:
        process_error("Payment method not found", ["implemented"])
    payment_method = user.payment_methods[payment_id]
    if payment_method.source == "certificate":
        process_error(
            "Certificate cannot be used to update reservation", ["implemented"]
        )
    elif payment_method.source == "gift_card" and payment_method.amount < total_price:
        process_error("Gift card balance is not enough", ["implemented"])

    # Deduct payment
    if payment_method.source == "gift_card":
        payment_method.amount -= total_price

    payment = None
    # Create payment if total price is not 0
    if total_price != 0:
        payment = Payment(
            payment_id=payment_id,
            amount=total_price,
        )
    return payment


def _get_free_baggage_allowance(membership: MembershipLevel, cabin: CabinClass) -> int:
    """Get the free baggage allowance based on membership level and cabin class."""
    additional = 0
    if membership == "gold":
        additional = 2
    elif membership == "silver":
        additional = 1
    if cabin == "basic_economy":
        return 0 + additional
    elif cabin == "economy":
        return 1 + additional
    elif cabin == "business":
        return 2 + additional


def _is_eligible_for_cancellation(
    reservation: Reservation, meet_insurance_policy: bool
) -> Tuple[bool, Optional[str]]:
    """Check if the reservation is eligible for cancellation."""
    booking_time = datetime.strptime(reservation.created_at, "%Y-%m-%dT%H:%M:%S")
    current_time = datetime.strptime(_get_datetime(), "%Y-%m-%dT%H:%M:%S")
    delta = current_time - booking_time
    if delta.total_seconds() < 24 * 3600:
        return True, None
    if reservation.cabin == "business":
        return True, None
    flight_status_list = []
    for flight in reservation.flights:
        flight_date_data = _get_flight_instance(
            flight_number=flight.flight_number, date=flight.date
        )
        if isinstance(flight_date_data, FlightDateStatusCancelled):
            return True, None
        flight_status_list.append(flight_date_data.status)
    if meet_insurance_policy and reservation.insurance == "yes":
        return True, None
    return False, (
        f"Reservation booking time: {reservation.created_at}, current time: {_get_datetime()}, time delta hours: {delta.total_seconds() / 3600:.2f}, "
        f"cabin: {reservation.cabin}, "
        f"flight statuses: {flight_status_list}, "
        f"insurance: {reservation.insurance}, meet_insurance_policy: {meet_insurance_policy}."
    )


def fetch_current_time() -> str:
    """
    Fetch the current system time.

    Returns:
        The current system time in ISO 8601 format.
    """
    return _get_datetime()


def compute_time_difference(
    time1: Annotated[
        str,
        "The first time in ISO 8601 format, such as '2024-05-01T10:00:00'.",
    ],
    time2: Annotated[
        str,
        "The second time in ISO 8601 format, such as '2024-05-01T15:30:00'.",
    ],
) -> dict[str, int]:
    """
    Compute the difference between two times. If time2 is later than time1, the result is positive; otherwise, it is negative.

    Returns:
        The difference of the 2 times, in hours and minutes.
    """
    fmt = "%Y-%m-%dT%H:%M:%S"
    dt1 = datetime.strptime(time1, fmt)
    dt2 = datetime.strptime(time2, fmt)
    delta = dt2 - dt1
    total_minutes = int(delta.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return {
        "hours": hours,
        "minutes": minutes,
    }


def compute_reservation_price(
    user_id: Annotated[
        str, "The ID of the user to book the reservation such as 'sara_doe_496'`."
    ],
    cabin: Annotated[
        CabinClass,
        "The cabin class such as 'basic_economy', 'economy', or 'business'.",
    ],
    flights: Annotated[
        List[FlightInfo | dict],
        "An array of objects containing details about each piece of flight.",
    ],
    passengers: Annotated[
        List[Passenger | dict],
        "An array of objects containing details about each passenger.",
    ],
    total_baggages: Annotated[
        int, "The total number of baggage items to book the reservation."
    ],
    nonfree_baggages: Annotated[
        int, "The number of non-free baggage items to book the reservation."
    ],
    insurance: Annotated[Insurance, "Whether the reservation has insurance."],
) -> int:
    """
    Compute the total price of a reservation without booking it.

    Returns:
        The total price of the reservation.
    """
    if all(isinstance(flight, dict) for flight in flights):
        flights = [FlightInfo(**flight) for flight in flights]
    if all(isinstance(passenger, dict) for passenger in passengers):
        passengers = [Passenger(**passenger) for passenger in passengers]

    if safeguard_config.API_CHECK and len(passengers) > 5:  # line: 73
        process_error(
            "Cannot book reservation for more than 5 passengers",
            ["api_check", "new_api"],
        )

    user = _get_user(user_id)

    if safeguard_config.API_CHECK:  # line: 82-94
        user_membership = user.membership
        free_baggage_allowance = _get_free_baggage_allowance(user_membership, cabin)
        passenger_num = len(passengers)
        if (
            total_baggages <= free_baggage_allowance * passenger_num
            and nonfree_baggages > 0
        ):
            process_error(
                f"Total baggages {total_baggages} within free allowance {free_baggage_allowance * passenger_num} = {free_baggage_allowance} (baggage num per person) * {passenger_num} (passenger count), but non-free baggages is {nonfree_baggages}. The non-free baggages should be 0.",
                ["api_check", "new_api"],
            )
        if (
            total_baggages > free_baggage_allowance * passenger_num
            and total_baggages
            != free_baggage_allowance * passenger_num + nonfree_baggages
        ):
            process_error(
                (
                    f"Total baggages {total_baggages} does not equal to free allowance {free_baggage_allowance * passenger_num} (computed by {free_baggage_allowance} (baggage num per person) * {passenger_num} (passenger count)) "
                    f"+ non-free baggages {nonfree_baggages}"
                ),
                ["api_check", "new_api"],
            )

    # Update flights and calculate price
    total_price = 0

    for flight_info in flights:
        flight_number = flight_info.flight_number
        flight_date_data = _get_flight_instance(
            flight_number=flight_number, date=flight_info.date
        )
        # Checking flight availability
        if not isinstance(flight_date_data, FlightDateStatusAvailable):
            process_error(
                f"Flight {flight_number} not available on date {flight_info.date}",
                ["implemented", "new_api"],
            )
        # Checking seat availability
        if flight_date_data.available_seats[cabin] < len(passengers):
            process_error(
                f"Not enough seats on flight {flight_number}",
                ["implemented", "new_api"],
            )
        # Calculate price
        price = flight_date_data.prices[cabin]
        total_price += price * len(passengers)

    # Add insurance fee
    if insurance == "yes":
        total_price += 30 * len(passengers)

    # Add baggage fee
    total_price += 50 * nonfree_baggages

    return total_price


def book_reservation(
    user_id: Annotated[
        str, "The ID of the user to book the reservation such as 'sara_doe_496'`."
    ],
    origin: Annotated[str, "The IATA code for the origin city such as 'SFO'."],
    destination: Annotated[
        str, "The IATA code for the destination city such as 'JFK'."
    ],
    flight_type: Annotated[
        FlightType, "The type of flight such as 'one_way' or 'round_trip'."
    ],
    cabin: Annotated[
        CabinClass,
        "The cabin class such as 'basic_economy', 'economy', or 'business'.",
    ],
    flights: Annotated[
        List[FlightInfo | dict],
        "An array of objects containing details about each piece of flight.",
    ],
    passengers: Annotated[
        List[Passenger | dict],
        "An array of objects containing details about each passenger.",
    ],
    payment_methods: Annotated[
        List[Payment | dict],
        "An array of objects containing details about each payment method.",
    ],
    total_baggages: Annotated[
        int, "The total number of baggage items to book the reservation."
    ],
    nonfree_baggages: Annotated[
        int, "The number of non-free baggage items to book the reservation."
    ],
    insurance: Annotated[Insurance, "Whether the reservation has insurance."],
) -> Reservation:
    """
    Book a reservation.
    """
    if all(isinstance(flight, dict) for flight in flights):
        flights = [FlightInfo(**flight) for flight in flights]
    if all(isinstance(passenger, dict) for passenger in passengers):
        passengers = [Passenger(**passenger) for passenger in passengers]
    if all(isinstance(payment_method, dict) for payment_method in payment_methods):
        payment_methods = [
            Payment(**payment_method) for payment_method in payment_methods
        ]

    if safeguard_config.API_CHECK and len(passengers) > 5:  # line: 73
        process_error(
            "Cannot book reservation for more than 5 passengers", ["api_check"]
        )

    user = _get_user(user_id)
    reservation_id = _get_new_reservation_id()

    if safeguard_config.API_CHECK:  # line: 82-94
        user_membership = user.membership
        free_baggage_allowance = _get_free_baggage_allowance(user_membership, cabin)
        passenger_num = len(passengers)
        if (
            total_baggages <= free_baggage_allowance * passenger_num
            and nonfree_baggages > 0
        ):
            process_error(
                (
                    f"Total baggages {total_baggages} within free allowance {free_baggage_allowance * passenger_num} = {free_baggage_allowance} (baggage num per person) * {passenger_num} (passenger count), "
                    f"but non-free baggages is {nonfree_baggages}. The non-free baggages should be 0."
                ),
                ["api_check"],
            )
        if (
            total_baggages > free_baggage_allowance * passenger_num
            and total_baggages
            != free_baggage_allowance * passenger_num + nonfree_baggages
        ):
            process_error(
                (
                    f"Total baggages {total_baggages} does not equal to free allowance {free_baggage_allowance * passenger_num} (computed by {free_baggage_allowance} (baggage num per person) * {passenger_num} (passenger count)) "
                    f"+ non-free baggages {nonfree_baggages}"
                ),
                ["api_check"],
            )

    reservation = Reservation(
        reservation_id=reservation_id,
        user_id=user_id,
        origin=origin,
        destination=destination,
        flight_type=flight_type,
        cabin=cabin,
        flights=[],
        passengers=deepcopy(passengers),
        payment_history=deepcopy(payment_methods),
        created_at=_get_datetime(),
        total_baggages=total_baggages,
        nonfree_baggages=nonfree_baggages,
        insurance=insurance,
    )

    # Update flights and calculate price
    total_price = 0
    all_flights_date_data: list[FlightDateStatusAvailable] = []

    ori_dst_list = []
    for flight_info in flights:
        flight_number = flight_info.flight_number
        flight = _get_flight(flight_number)
        flight_date_data = _get_flight_instance(
            flight_number=flight_number, date=flight_info.date
        )
        # Checking flight availability
        if not isinstance(flight_date_data, FlightDateStatusAvailable):
            process_error(
                f"Flight {flight_number} not available on date {flight_info.date}",
                ["implemented"],
            )
        # Checking seat availability
        if flight_date_data.available_seats[cabin] < len(passengers):
            process_error(
                f"Not enough seats on flight {flight_number}", ["implemented"]
            )
        # Calculate price
        price = flight_date_data.prices[cabin]
        # Update reservation
        reservation.flights.append(
            ReservationFlight(
                origin=flight.origin,
                destination=flight.destination,
                flight_number=flight_number,
                date=flight_info.date,
                price=price,
            )
        )
        all_flights_date_data.append(flight_date_data)
        total_price += price * len(passengers)

    # Add insurance fee
    if insurance == "yes":
        total_price += 30 * len(passengers)

    # Add baggage fee
    total_price += 50 * nonfree_baggages

    count_payment_type = {
        "credit_card": 0,
        "gift_card": 0,
        "certificate": 0,
    }
    payment_method_set = set()

    for payment_method in payment_methods:
        payment_id = payment_method.payment_id
        amount = payment_method.amount
        if payment_id not in user.payment_methods:
            process_error(f"Payment method {payment_id} not found", ["implemented"])

        user_payment_method = user.payment_methods[payment_id]
        count_payment_type[user_payment_method.source] += 1
        if user_payment_method.source in {"gift_card", "certificate"}:
            if user_payment_method.amount < amount:
                process_error(
                    f"Not enough balance in payment method {payment_id}",
                    ["implemented"],
                )
        if safeguard_config.API_CHECK and payment_id in payment_method_set:
            process_error(
                f"Duplicate payment method {payment_id} in payment methods",
                ["api_check"],
            )
        payment_method_set.add(payment_id)

    if safeguard_config.API_CHECK:  # line: 78
        if count_payment_type["certificate"] > 1:
            process_error(
                f"Each reservation can use at most one travel certificate. You have used {count_payment_type['certificate']} certificates.",
                ["api_check"],
            )
        if count_payment_type["credit_card"] > 1:
            process_error(
                f"Each reservation can use at most one credit card. You have used {count_payment_type['credit_card']} credit cards.",
                ["api_check"],
            )
        if count_payment_type["gift_card"] > 3:
            process_error(
                f"Each reservation can use at most three gift cards. You have used {count_payment_type['gift_card']} gift cards.",
                ["api_check"],
            )
    if safeguard_config.API_CHECK:  # line: unspecified (commonsense)
        if origin != reservation.flights[0].origin:
            process_error(
                "Origin does not match the first flight's origin", ["api_check"]
            )
        if (
            flight_type == "one_way"
            and destination != reservation.flights[-1].destination
        ):
            process_error(
                (
                    "As a one-way flight, destination must match the last flight's destination. The last flight's destination is "
                    f"{reservation.flights[-1].destination}, but the destination provided is {destination}."
                ),
                ["api_check"],
            )
        if (
            flight_type == "round_trip"
            and origin != reservation.flights[-1].destination
        ):
            process_error(
                (
                    "As a round-trip flight, origin must match the last flight's destination. The last flight's destination is "
                    f"{reservation.flights[-1].destination}, but the origin provided is {origin}."
                ),
                ["api_check"],
            )
        if flight_type == "round_trip":
            has_flight_end_at_destination = False
            has_flight_start_at_destination = False
            ori_dst_list = []
            for res_flight in reservation.flights:
                if res_flight.destination == destination:
                    has_flight_end_at_destination = True
                if res_flight.origin == destination:
                    has_flight_start_at_destination = True
                ori_dst_list.append((res_flight.origin, res_flight.destination))
            if not (has_flight_end_at_destination and has_flight_start_at_destination):
                process_error(
                    (
                        "Round trip reservation must have flights that go to and return from the destination. "
                        f"The current origin-destination pairs are: {ori_dst_list}."
                    ),
                    ["api_check"],
                )

    total_payment = sum(payment.amount for payment in payment_methods)
    if total_payment != total_price:
        process_error(
            f"Payment amount does not add up, total price is {total_price}, but paid {total_payment}",
            ["implemented"],
        )

    # if checks pass, deduct payment
    for payment_method in payment_methods:
        payment_id = payment_method.payment_id
        amount = payment_method.amount
        user_payment_method = user.payment_methods[payment_id]
        if user_payment_method.source == "gift_card":
            user_payment_method.amount -= amount
        elif user_payment_method.source == "certificate":
            user.payment_methods.pop(payment_id)

    # Update DB
    for flight_date_data in all_flights_date_data:
        flight_date_data.available_seats[cabin] -= len(passengers)
    db.reservations[reservation_id] = reservation
    db.users[user_id].reservations.append(reservation_id)
    return reservation


def calculate(
    expression: Annotated[
        str,
        "The mathematical expression to calculate, such as '2 + 2'. The expression can contain numbers, operators (+, -, *, /), parentheses, and spaces.",
    ],
) -> str:
    """
    Calculate the result of a mathematical expression.

    Returns:
        The result of the mathematical expression.

    Raises:
        ValueError: If the expression is invalid.
    """
    if not all(char in "0123456789+-*/(). " for char in expression):
        process_error("Invalid characters in expression", ["implemented"])
    return str(round(float(eval(expression, {"__builtins__": None}, {})), 2))


if safeguard_config.API_REDESIGN:  # line: 139

    def cancel_reservation(
        user_id: Annotated[str, "The ID of the user cancelling the reservation."],
        reservation_id: Annotated[str, "The reservation ID, such as 'ZFA04Y'."],
        reason: Annotated[CancellationReason, "The reason for cancellation."],
        meet_cancellation_insurance_policy: Annotated[
            bool,
            "Whether the cancellation reason is covered by the insurance policy (health or weather issue). If so, set to true; otherwise, set to false.",
        ],
    ) -> Reservation:
        """
        Cancel the whole reservation.

        Returns:
            The updated reservation.

        Raises:
            ValueError: If the reservation is not found.
        """
        user = _get_user(user_id)
        reservation = _get_reservation(reservation_id)

        if safeguard_config.API_CHECK and reservation.user_id != user_id:  # line: 106
            process_error(
                "User does not own the reservation", ["api_check", "api_redesign"]
            )

        if safeguard_config.API_CHECK:  # line: 139
            if reason not in {"change_of_plan", "airline_cancelled_flight", "other"}:
                process_error(
                    "Invalid reason for cancellation. Must be one of 'change_of_plan', 'airline_cancelled_flight', or 'other'.",
                    ["api_check", "api_redesign"],
                )
        if safeguard_config.API_CHECK:  # line: 141
            for res_flight in reservation.flights:
                flight_date_data = _get_flight_instance(
                    flight_number=res_flight.flight_number, date=res_flight.date
                )
                if isinstance(flight_date_data, FlightDateStatusLanded) or isinstance(
                    flight_date_data, FlightDataStatusFlying
                ):
                    process_error(
                        f"Cannot cancel reservation with flight {res_flight.flight_number} already departed or landed. Must transfer to human agent for further assistance.",
                        ["api_check", "api_redesign"],
                    )
        if safeguard_config.API_CHECK:  # line: 144-147
            assertion, result_msg = _is_eligible_for_cancellation(
                reservation, meet_cancellation_insurance_policy
            )
            if not assertion:
                process_error(
                    (
                        "Reservation is not eligible for cancellation based on the airline's cancellation policy. "
                        "The policy states that cancellations are only allowed if made within 24 hours of booking, "
                        "if the flight is cancelled by the airline, if the booking is in business class, "
                        "or if the cancellation reason is covered by the insurance policy and the reservation has insurance. "
                    )
                    + (result_msg if result_msg is not None else ""),
                    ["api_check", "api_redesign"],
                )

        if safeguard_config.API_REDESIGN:  # line: 165
            reservation.has_delay_history = False
            for flight in reservation.flights:
                flight_date_data = _get_flight_instance(
                    flight_number=flight.flight_number, date=flight.date
                )
                if isinstance(flight_date_data, FlightDateStatusDelayed):
                    reservation.has_delay_history = True
                    break

        # LOGGER.debug(reservation.model_dump_json(indent=4))
        # reverse the payment
        refunds = []
        for payment in reservation.payment_history:
            refunds.append(
                Payment(
                    payment_id=payment.payment_id,
                    amount=-payment.amount,
                )
            )
        reservation.payment_history.extend(refunds)
        reservation.status = "cancelled"
        # LOGGER.debug(_get_reservation(reservation_id).model_dump_json(indent=4))
        # Release seats
        # LOGGER.warning("Seats release not implemented for cancellation!!!")
        return reservation

else:

    def cancel_reservation(
        reservation_id: Annotated[str, "The reservation ID, such as 'ZFA04Y'."],
    ) -> Reservation:
        """
        Cancel the whole reservation.

        Returns:
            The updated reservation.

        Raises:
            ValueError: If the reservation is not found.
        """
        reservation = _get_reservation(reservation_id)

        if safeguard_config.API_CHECK:  # line: 141
            for res_flight in reservation.flights:
                flight_date_data = _get_flight_instance(
                    flight_number=res_flight.flight_number, date=res_flight.date
                )
                if isinstance(flight_date_data, FlightDateStatusLanded) or isinstance(
                    flight_date_data, FlightDataStatusFlying
                ):
                    process_error(
                        f"Cannot cancel reservation with flight {res_flight.flight_number} already departed or landed. Must transfer to human agent for further assistance.",
                        ["api_check"],
                    )
        if safeguard_config.API_CHECK:  # line: 144-147
            assertion, result_msg = _is_eligible_for_cancellation(
                reservation, meet_insurance_policy=True
            )
            if not assertion:
                process_error(
                    (
                        "Reservation is not eligible for cancellation based on the airline's cancellation policy. "
                        "The policy states that cancellations are only allowed if made within 24 hours of booking, "
                        "if the flight is cancelled by the airline, if the booking is in business class, "
                        "or if the cancellation reason is covered by the insurance policy and the reservation has insurance. "
                    )
                    + (result_msg if result_msg is not None else ""),
                    ["api_check"],
                )

        # LOGGER.debug(reservation.model_dump_json(indent=4))
        # reverse the payment
        refunds = []
        for payment in reservation.payment_history:
            refunds.append(
                Payment(
                    payment_id=payment.payment_id,
                    amount=-payment.amount,
                )
            )
        reservation.payment_history.extend(refunds)
        reservation.status = "cancelled"
        # LOGGER.debug(_get_reservation(reservation_id).model_dump_json(indent=4))
        # Release seats
        # LOGGER.warning("Seats release not implemented for cancellation!!!")
        return reservation


if safeguard_config.API_REDESIGN:  # line: 106

    def get_reservation_details(
        user_id: Annotated[str, "The ID of the user retrieving the reservation."],
        reservation_id: Annotated[str, "The reservation ID, such as '8JX2WO'."],
    ) -> Reservation:
        """
        Get the details of a reservation.

        Returns:
            The reservation details.

        Raises:
            ValueError: If the reservation is not found.
            ValueError: If the user does not own the reservation.
        """
        user = _get_user(user_id)
        reservation = _get_reservation(reservation_id)
        if safeguard_config.API_CHECK and reservation.user_id != user_id:  # line: 106
            process_error(
                "User does not own the reservation", ["api_check", "api_redesign"]
            )
        return reservation

else:

    def get_reservation_details(
        reservation_id: Annotated[str, "The reservation ID, such as '8JX2WO'."],
    ) -> Reservation:
        """
        Get the details of a reservation.

        Returns:
            The reservation details.

        Raises:
            ValueError: If the reservation is not found.
        """
        return _get_reservation(reservation_id)


def get_user_details(
    user_id: Annotated[str, "The user ID, such as 'sara_doe_496'."],
) -> User:
    """
    Get the details of a user, including their reservations.

    Returns:
        The user details.

    Raises:
        ValueError: If the user is not found.
    """
    return _get_user(user_id)


def list_all_airports() -> AirportInfo:
    """Returns a list of all available airports.

    Returns:
        A dictionary mapping IATA codes to AirportInfo objects.
    """
    return [
        AirportCode(iata="SFO", city="San Francisco"),
        AirportCode(iata="JFK", city="New York"),
        AirportCode(iata="LAX", city="Los Angeles"),
        AirportCode(iata="ORD", city="Chicago"),
        AirportCode(iata="DFW", city="Dallas"),
        AirportCode(iata="DEN", city="Denver"),
        AirportCode(iata="SEA", city="Seattle"),
        AirportCode(iata="ATL", city="Atlanta"),
        AirportCode(iata="MIA", city="Miami"),
        AirportCode(iata="BOS", city="Boston"),
        AirportCode(iata="PHX", city="Phoenix"),
        AirportCode(iata="IAH", city="Houston"),
        AirportCode(iata="LAS", city="Las Vegas"),
        AirportCode(iata="MCO", city="Orlando"),
        AirportCode(iata="EWR", city="Newark"),
        AirportCode(iata="CLT", city="Charlotte"),
        AirportCode(iata="MSP", city="Minneapolis"),
        AirportCode(iata="DTW", city="Detroit"),
        AirportCode(iata="PHL", city="Philadelphia"),
        AirportCode(iata="LGA", city="LaGuardia"),
    ]


def search_direct_flight(
    origin: Annotated[str, "The origin city airport in three letters, such as 'JFK'."],
    destination: Annotated[
        str, "The destination city airport in three letters, such as 'LAX'."
    ],
    date: Annotated[
        str, "The date of the flight in the format 'YYYY-MM-DD', such as '2024-01-01'."
    ],
) -> list[DirectFlight]:
    """
    Search for direct flights between two cities on a specific date.

    Returns:
        The direct flights between the two cities on the specific date.
    """
    return _search_direct_flight(date=date, origin=origin, destination=destination)


def search_onestop_flight(
    origin: Annotated[str, "The origin city airport in three letters, such as 'JFK'."],
    destination: Annotated[
        str, "The destination city airport in three letters, such as 'LAX'."
    ],
    date: Annotated[
        str, "The date of the flight in the format 'YYYY-MM-DD', such as '2024-05-01'."
    ],
) -> list[tuple[DirectFlight, DirectFlight]]:
    """
    Search for one-stop flights between two cities on a specific date.

    Returns:
        A list of pairs of DirectFlight objects.
    """
    results = []
    for result1 in _search_direct_flight(date=date, origin=origin, destination=None):
        result1.date = date
        date2 = (
            f"2024-05-{int(date[-2:]) + 1}"
            if "+1" in result1.scheduled_arrival_time_est
            else date
        )
        for result2 in _search_direct_flight(
            date=date2,
            origin=result1.destination,
            destination=destination,
            leave_after=result1.scheduled_arrival_time_est,
        ):
            result2.date = date2
            results.append([result1, result2])
    return results


def think(thought: Annotated[str, "A thought to think about."]) -> str:
    """
    Use the tool to think about something.
    It will not obtain new information or change the database, but just append the thought to the log.
    Use it when complex reasoning or some cache memory is needed.

    Returns:
        Empty string
    """
    return ""


def transfer_to_human_agents(
    summary: Annotated[str, "A summary of the user's issue."],
) -> str:
    """
    Transfer the user to a human agent, with a summary of the user's issue.
    Only transfer if
        -  the user explicitly asks for a human agent
        -  given the policy and the available tools, you cannot solve the user's issue.

    Returns:
        A message indicating the user has been transferred to a human agent.
    """
    return "Transfer successful"


def compute_update_reservation_baggages_price(
    user_id: Annotated[str, "The ID of the user updating the reservation."],
    reservation_id: Annotated[str, "The reservation ID, such as 'ZFA04Y'."],
    total_baggages: Annotated[
        int,
        "The updated total number of baggage items included in the reservation.",
    ],
    nonfree_baggages: Annotated[
        int,
        "The updated number of non-free baggage items included in the reservation.",
    ],
) -> int:
    """
    Compute the price for updating the baggage information of a reservation. This does not actually update the reservation.

    Returns:
        The price for updating the baggage information.
    """
    reservation = _get_reservation(reservation_id)
    user = _get_user(user_id)
    if safeguard_config.API_CHECK and reservation.user_id != user_id:  # line: 106
        process_error("User does not own the reservation", ["api_check", "new_api"])

    if safeguard_config.API_CHECK:  # line: 123
        if nonfree_baggages < reservation.nonfree_baggages:
            process_error(
                (
                    "Can only add or keep, not reduce, the number of non-free baggages. The total baggages may be added as free-baggages. "
                    f"Current non-free baggages: {reservation.nonfree_baggages}, requested non-free baggages: {nonfree_baggages}. "
                    f"Current total baggages: {reservation.total_baggages}, requested total baggages: {total_baggages}."
                ),
                ["api_check", "new_api"],
            )
    if safeguard_config.API_CHECK:  # line: 82-94
        free_baggage_allowance = _get_free_baggage_allowance(
            user.membership, reservation.cabin
        )
        passenger_num = len(reservation.passengers)
        if (
            total_baggages <= free_baggage_allowance * passenger_num
            and nonfree_baggages > 0
        ):
            process_error(
                (
                    f"Total baggages {total_baggages} within free allowance {free_baggage_allowance * passenger_num} = {free_baggage_allowance} (baggage num per person) * {passenger_num} (passenger count), "
                    f"but non-free baggages is {nonfree_baggages}. The non-free baggages should be 0. The additional bag should be added as free-baggages."
                ),
                ["api_check", "new_api"],
            )
        if (
            total_baggages > free_baggage_allowance * passenger_num
            and total_baggages
            != free_baggage_allowance * passenger_num + nonfree_baggages
        ):
            process_error(
                (
                    f"Total baggages {total_baggages} does not equal to free allowance {free_baggage_allowance * passenger_num} (computed by {free_baggage_allowance} (baggage num per person) * {passenger_num} (passenger count)) "
                    f"+ non-free baggages {nonfree_baggages}"
                ),
                ["api_check", "new_api"],
            )

    # Calculate price
    total_price = 50 * max(0, nonfree_baggages - reservation.nonfree_baggages)
    return total_price


if safeguard_config.API_REDESIGN:  # line: 106

    def update_reservation_baggages(
        user_id: Annotated[str, "The ID of the user updating the reservation."],
        reservation_id: Annotated[str, "The reservation ID, such as 'ZFA04Y'."],
        total_baggages: Annotated[
            int,
            "The updated total number of baggage items included in the reservation.",
        ],
        nonfree_baggages: Annotated[
            int,
            "The updated number of non-free baggage items included in the reservation.",
        ],
        payment_id: Annotated[
            str,
            "The payment id stored in user profile, such as 'credit_card_7815826', 'gift_card_7815826', 'certificate_7815826'.",
        ],
        payment_amount: Annotated[
            int,
            "The payment amount to be paid for the baggage update.",
        ],
    ) -> Reservation:
        """
        Update the baggage information of a reservation.

        Returns:
            The updated reservation.

        Raises:
            ValueError: If the user does not own the reservation.
            ValueError: If the reservation is not found.
            ValueError: If the user is not found.
            ValueError: If the payment method is not found.
            ValueError: If the certificate cannot be used to update reservation.
            ValueError: If the gift card balance is not enough.
        """
        reservation = _get_reservation(reservation_id)
        user = _get_user(user_id)
        if safeguard_config.API_CHECK and reservation.user_id != user_id:
            process_error(
                "User does not own the reservation", ["api_check", "api_redesign"]
            )

        if safeguard_config.API_CHECK:  # line: 123
            if nonfree_baggages < reservation.nonfree_baggages:
                process_error(
                    (
                        "Can only add or keep, not reduce, the number of non-free baggages. The total baggages may be added as free-baggages. "
                        f"Current non-free baggages: {reservation.nonfree_baggages}, requested non-free baggages: {nonfree_baggages}. "
                        f"Current total baggages: {reservation.total_baggages}, requested total baggages: {total_baggages}."
                    ),
                    ["api_check", "api_redesign"],
                )
        if safeguard_config.API_CHECK:  # line: 82-94
            free_baggage_allowance = _get_free_baggage_allowance(
                user.membership, reservation.cabin
            )
            passenger_num = len(reservation.passengers)
            if (
                total_baggages <= free_baggage_allowance * passenger_num
                and nonfree_baggages > 0
            ):
                process_error(
                    (
                        f"Total baggages {total_baggages} within free allowance {free_baggage_allowance * passenger_num} = {free_baggage_allowance} (baggage num per person) * {passenger_num} (passenger count), "
                        f"but non-free baggages is {nonfree_baggages}. The non-free baggages should be 0. The additional bag should be added as free-baggages."
                    ),
                    ["api_check", "api_redesign"],
                )
            if (
                total_baggages > free_baggage_allowance * passenger_num
                and total_baggages
                != free_baggage_allowance * passenger_num + nonfree_baggages
            ):
                process_error(
                    (
                        f"Total baggages {total_baggages} does not equal to free allowance {free_baggage_allowance * passenger_num} (computed by {free_baggage_allowance} (baggage num per person) * {passenger_num} (passenger count)) "
                        f"+ non-free baggages {nonfree_baggages}"
                    ),
                    ["api_check", "api_redesign"],
                )

        # Calculate price
        total_price = 50 * max(0, nonfree_baggages - reservation.nonfree_baggages)

        if safeguard_config.API_CHECK and total_price != payment_amount:  # line: 166
            process_error(
                f"Payment amount {payment_amount} does not match the calculated price {total_price} for the baggage update.",
                ["api_check", "api_redesign"],
            )

        # Create payment
        payment = _payment_for_update(user, payment_id, total_price)
        if payment is not None:
            reservation.payment_history.append(payment)

        # Update reservation
        reservation.total_baggages = total_baggages
        reservation.nonfree_baggages = nonfree_baggages

        return reservation

else:

    def update_reservation_baggages(
        reservation_id: Annotated[str, "The reservation ID, such as 'ZFA04Y'."],
        total_baggages: Annotated[
            int,
            "The updated total number of baggage items included in the reservation.",
        ],
        nonfree_baggages: Annotated[
            int,
            "The updated number of non-free baggage items included in the reservation.",
        ],
        payment_id: Annotated[
            str,
            "The payment id stored in user profile, such as 'credit_card_7815826', 'gift_card_7815826', 'certificate_7815826'.",
        ],
    ) -> Reservation:
        """
        Update the baggage information of a reservation.

        Returns:
            The updated reservation.

        Raises:
            ValueError: If the reservation is not found.
            ValueError: If the user is not found.
            ValueError: If the payment method is not found.
            ValueError: If the certificate cannot be used to update reservation.
            ValueError: If the gift card balance is not enough.
        """
        reservation = _get_reservation(reservation_id)
        user = _get_user(reservation.user_id)

        if safeguard_config.API_CHECK:  # line: 123
            if nonfree_baggages < reservation.nonfree_baggages:
                process_error(
                    (
                        "Can only add or keep, not reduce, the number of non-free baggages. The total baggages may be added as free-baggages. "
                        f"Current non-free baggages: {reservation.nonfree_baggages}, requested non-free baggages: {nonfree_baggages}. "
                        f"Current total baggages: {reservation.total_baggages}, requested total baggages: {total_baggages}."
                    ),
                    ["api_check"],
                )
        if safeguard_config.API_CHECK:  # line: 82-94
            free_baggage_allowance = _get_free_baggage_allowance(
                user.membership, reservation.cabin
            )
            passenger_num = len(reservation.passengers)
            if (
                total_baggages <= free_baggage_allowance * passenger_num
                and nonfree_baggages > 0
            ):
                process_error(
                    (
                        f"Total baggages {total_baggages} within free allowance {free_baggage_allowance * passenger_num} = {free_baggage_allowance} (baggage num per person) * {passenger_num} (passenger count), "
                        f"but non-free baggages is {nonfree_baggages}. The non-free baggages should be 0. The additional bag should be added as free-baggages."
                    ),
                    ["api_check"],
                )
            if (
                total_baggages > free_baggage_allowance * passenger_num
                and total_baggages
                != free_baggage_allowance * passenger_num + nonfree_baggages
            ):
                process_error(
                    (
                        f"Total baggages {total_baggages} does not equal to free allowance {free_baggage_allowance * passenger_num} (computed by {free_baggage_allowance} (baggage num per person) * {passenger_num} (passenger count)) "
                        f"+ non-free baggages {nonfree_baggages}"
                    ),
                    ["api_check"],
                )

        # Calculate price
        total_price = 50 * max(0, nonfree_baggages - reservation.nonfree_baggages)

        # Create payment
        payment = _payment_for_update(user, payment_id, total_price)
        if payment is not None:
            reservation.payment_history.append(payment)

        # Update reservation
        reservation.total_baggages = total_baggages
        reservation.nonfree_baggages = nonfree_baggages

        return reservation


def compute_update_reservation_flights_price(
    user_id: Annotated[str, "The ID of the user updating the reservation."],
    reservation_id: Annotated[str, "The reservation ID, such as 'ZFA04Y'."],
    cabin: Annotated[CabinClass, "The cabin class of the reservation"],
    flights: Annotated[
        List[FlightInfo | dict],
        "An array of objects containing details about each piece of flight in the ENTIRE new reservation. Even if the a flight segment is not changed, it should still be included in the array.",
    ],
) -> int:
    """
    Compute the price difference if updating the flight information of a reservation. This does not update the reservation. A positive value indicates an additional cost, while a negative value indicates a refund.

    Returns:
        The price difference.

    Raises:
        ValueError: If the user does not own the reservation.
        ValueError: If the reservation is not found.
        ValueError: If the user is not found.
    """
    if all(isinstance(flight, dict) for flight in flights):
        flights = [FlightInfo(**flight) for flight in flights]

    if safeguard_config.API_CHECK and len(flights) == 0:  # line: 111
        process_error("Flights list cannot be empty", ["api_check", "new_api"])

    reservation = _get_reservation(reservation_id)
    user = _get_user(user_id)
    if safeguard_config.API_CHECK and reservation.user_id != user_id:
        process_error("User does not own the reservation", ["api_check", "new_api"])

    if safeguard_config.API_CHECK and cabin != reservation.cabin:  # line: 116
        # check if flight have already been flown
        for reservation_flight in reservation.flights:
            flight_date_data = _get_flight_instance(
                flight_number=reservation_flight.flight_number,
                date=reservation_flight.date,
            )
            if isinstance(flight_date_data, FlightDateStatusLanded) or isinstance(
                flight_date_data, FlightDataStatusFlying
            ):
                process_error(
                    (
                        "Cannot change cabin class for already flown flights. "
                        f"Flight {reservation_flight.flight_number} on date {reservation_flight.date} has already been flown."
                    ),
                    ["api_check", "new_api"],
                )

    # update flights and calculate price
    total_price = 0
    reservation_flights = []
    change_flights = False
    for flight_info in flights:
        # if existing flight, keep it
        matching_reservation_flight = next(
            (
                reservation_flight
                for reservation_flight in reservation.flights
                if reservation_flight.flight_number == flight_info.flight_number
                and reservation_flight.date == flight_info.date
                and cabin == reservation.cabin
            ),
            None,
        )
        if matching_reservation_flight:
            total_price += matching_reservation_flight.price * len(
                reservation.passengers
            )
            reservation_flights.append(matching_reservation_flight)
            continue

        matching_reservation_except_cabin = next(
            (
                reservation_flight
                for reservation_flight in reservation.flights
                if reservation_flight.flight_number == flight_info.flight_number
                and reservation_flight.date == flight_info.date
            ),
            None,
        )

        if not matching_reservation_except_cabin:
            change_flights = True
        # If new flight:
        flight = _get_flight(flight_info.flight_number)
        # Check flight availability
        flight_date_data = _get_flight_instance(
            flight_number=flight_info.flight_number,
            date=flight_info.date,
        )
        if not isinstance(flight_date_data, FlightDateStatusAvailable):
            process_error(
                f"Flight {flight_info.flight_number} not available on date {flight_info.date}",
                ["implemented", "new_api"],
            )

        # Check seat availability
        if flight_date_data.available_seats[cabin] < len(reservation.passengers):
            process_error(
                f"Not enough seats on flight {flight_info.flight_number}",
                ["implemented", "new_api"],
            )

        # Calculate price and add to reservation
        reservation_flight = ReservationFlight(
            flight_number=flight_info.flight_number,
            date=flight_info.date,
            price=flight_date_data.prices[cabin],
            origin=flight.origin,
            destination=flight.destination,
        )
        total_price += reservation_flight.price * len(reservation.passengers)
        reservation_flights.append(reservation_flight)

    if safeguard_config.API_CHECK:  # line: 111
        if reservation.origin != reservation_flights[0].origin:
            process_error(
                f"The reservation origin {reservation.origin} does not match the first flight's origin {reservation_flights[0].origin}",
                ["api_check", "new_api"],
            )
        if (
            reservation.flight_type == "one_way"
            and reservation.destination != reservation_flights[-1].destination
        ):
            process_error(
                (
                    "As a one-way flight, destination must match the last flight's destination. "
                    f"The last flight's destination is {reservation_flights[-1].destination}, but the reservation destination is {reservation.destination}."
                ),
                ["api_check", "new_api"],
            )
        if (
            reservation.flight_type == "round_trip"
            and reservation.origin != reservation_flights[-1].destination
        ):
            process_error(
                (
                    "As a round-trip flight, origin must match the last flight's destination. "
                    f"The last flight's destination is {reservation_flights[-1].destination}, but the reservation origin is {reservation.origin}."
                ),
                ["api_check", "new_api"],
            )
        if reservation.flight_type == "round_trip":
            has_flight_end_at_destination = False
            has_flight_start_at_destination = False
            ori_dst_list = []
            for res_flight in reservation_flights:
                if res_flight.destination == reservation.destination:
                    has_flight_end_at_destination = True
                if res_flight.origin == reservation.destination:
                    has_flight_start_at_destination = True
                ori_dst_list.append((res_flight.origin, res_flight.destination))
            if not (has_flight_end_at_destination and has_flight_start_at_destination):
                process_error(
                    (
                        "Round trip reservation must have flights that go to and return from the destination. "
                        f" The reservation destination is {reservation.destination}. The current origin-destination pairs are: {ori_dst_list}."
                    ),
                    ["api_check", "new_api"],
                )

    if (
        safeguard_config.API_CHECK
        and change_flights
        and reservation.cabin == "basic_economy"
    ):  # line: 110
        process_error(
            "Cannot change flights when cabin class is basic_economy",
            ["api_check", "new_api"],
        )

    # Deduct amount already paid for reservation
    total_price -= sum(flight.price for flight in reservation.flights) * len(
        reservation.passengers
    )
    return total_price


if safeguard_config.API_REDESIGN:  # line: 106

    def update_reservation_flights(
        user_id: Annotated[str, "The ID of the user updating the reservation."],
        reservation_id: Annotated[str, "The reservation ID, such as 'ZFA04Y'."],
        cabin: Annotated[CabinClass, "The cabin class of the reservation"],
        flights: Annotated[
            List[FlightInfo | dict],
            "An array of objects containing details about each piece of flight in the ENTIRE new reservation. Even if the a flight segment is not changed, it should still be included in the array.",
        ],
        payment_id: Annotated[
            str,
            "The payment id stored in user profile, such as 'credit_card_7815826', 'gift_card_7815826', 'certificate_7815826'.",
        ],
        payment_amount: Annotated[
            int,
            "The amount to be paid for the update. If negative, it indicates a refund amount.",
        ],
    ) -> Reservation:
        """
        Update the flight information of a reservation.

        Returns:
            The updated reservation.

        Raises:
            ValueError: If the user does not own the reservation.
            ValueError: If the reservation is not found.
            ValueError: If the user is not found.
            ValueError: If the payment method is not found.
            ValueError: If the certificate cannot be used to update reservation.
            ValueError: If the gift card balance is not enough.
        """
        if all(isinstance(flight, dict) for flight in flights):
            flights = [FlightInfo(**flight) for flight in flights]

        if safeguard_config.API_CHECK and len(flights) == 0:  # line: 111
            process_error("Flights list cannot be empty", ["api_check", "api_redesign"])

        reservation = _get_reservation(reservation_id)
        user = _get_user(user_id)
        if safeguard_config.API_CHECK and reservation.user_id != user_id:
            process_error(
                "User does not own the reservation", ["api_check", "api_redesign"]
            )

        if safeguard_config.API_CHECK and cabin != reservation.cabin:  # line: 116
            # check if flight have already been flown
            for reservation_flight in reservation.flights:
                flight_date_data = _get_flight_instance(
                    flight_number=reservation_flight.flight_number,
                    date=reservation_flight.date,
                )
                if isinstance(flight_date_data, FlightDateStatusLanded) or isinstance(
                    flight_date_data, FlightDataStatusFlying
                ):
                    process_error(
                        (
                            "Cannot change cabin class for already flown flights. "
                            f"Flight {reservation_flight.flight_number} on date {reservation_flight.date} has already been flown."
                        ),
                        ["api_check", "api_redesign"],
                    )
        # update flights and calculate price
        total_price = 0
        reservation_flights = []
        change_flights = False
        for flight_info in flights:
            # if existing flight, keep it
            matching_reservation_flight = next(
                (
                    reservation_flight
                    for reservation_flight in reservation.flights
                    if reservation_flight.flight_number == flight_info.flight_number
                    and reservation_flight.date == flight_info.date
                    and cabin == reservation.cabin
                ),
                None,
            )
            if matching_reservation_flight:
                total_price += matching_reservation_flight.price * len(
                    reservation.passengers
                )
                reservation_flights.append(matching_reservation_flight)
                continue

            matching_reservation_except_cabin = next(
                (
                    reservation_flight
                    for reservation_flight in reservation.flights
                    if reservation_flight.flight_number == flight_info.flight_number
                    and reservation_flight.date == flight_info.date
                ),
                None,
            )

            if not matching_reservation_except_cabin:
                change_flights = True
            # If new flight:
            flight = _get_flight(flight_info.flight_number)
            # Check flight availability
            flight_date_data = _get_flight_instance(
                flight_number=flight_info.flight_number,
                date=flight_info.date,
            )
            if not isinstance(flight_date_data, FlightDateStatusAvailable):
                process_error(
                    f"Flight {flight_info.flight_number} not available on date {flight_info.date}",
                    ["implemented", "api_redesign"],
                )

            # Check seat availability
            if flight_date_data.available_seats[cabin] < len(reservation.passengers):
                process_error(
                    f"Not enough seats on flight {flight_info.flight_number}",
                    ["implemented", "api_redesign"],
                )

            # Calculate price and add to reservation
            reservation_flight = ReservationFlight(
                flight_number=flight_info.flight_number,
                date=flight_info.date,
                price=flight_date_data.prices[cabin],
                origin=flight.origin,
                destination=flight.destination,
            )
            total_price += reservation_flight.price * len(reservation.passengers)
            reservation_flights.append(reservation_flight)

        if safeguard_config.API_CHECK:  # line: 111
            if reservation.origin != reservation_flights[0].origin:
                process_error(
                    f"The reservation origin {reservation.origin} does not match the first flight's origin {reservation_flights[0].origin}",
                    ["api_check", "api_redesign"],
                )
            if (
                reservation.flight_type == "one_way"
                and reservation.destination != reservation_flights[-1].destination
            ):
                process_error(
                    (
                        "As a one-way flight, destination must match the last flight's destination. "
                        f"The last flight's destination is {reservation_flights[-1].destination}, but the reservation destination is {reservation.destination}."
                    ),
                    ["api_check", "api_redesign"],
                )
            if (
                reservation.flight_type == "round_trip"
                and reservation.origin != reservation_flights[-1].destination
            ):
                process_error(
                    (
                        "As a round-trip flight, origin must match the last flight's destination. "
                        f"The last flight's destination is {reservation_flights[-1].destination}, but the reservation origin is {reservation.origin}."
                    ),
                    ["api_check", "api_redesign"],
                )
            if reservation.flight_type == "round_trip":
                has_flight_end_at_destination = False
                has_flight_start_at_destination = False
                ori_dst_list = []
                for res_flight in reservation_flights:
                    if res_flight.destination == reservation.destination:
                        has_flight_end_at_destination = True
                    if res_flight.origin == reservation.destination:
                        has_flight_start_at_destination = True
                    ori_dst_list.append((res_flight.origin, res_flight.destination))
                if not (
                    has_flight_end_at_destination and has_flight_start_at_destination
                ):
                    process_error(
                        (
                            "Round trip reservation must have flights that go to and return from the destination. "
                            f" The reservation destination is {reservation.destination}. The current origin-destination pairs are: {ori_dst_list}."
                        ),
                        ["api_check", "api_redesign"],
                    )

        if (
            safeguard_config.API_CHECK
            and change_flights
            and reservation.cabin == "basic_economy"
        ):  # line: 110
            process_error(
                "Cannot change flights when cabin class is basic_economy",
                ["api_check", "api_redesign"],
            )

        if safeguard_config.API_REDESIGN:  # line: 165
            reservation.has_delay_history = False
            for flight in reservation.flights:
                flight_date_data = _get_flight_instance(
                    flight_number=flight.flight_number, date=flight.date
                )
                if isinstance(flight_date_data, FlightDateStatusDelayed):
                    reservation.has_delay_history = True
                    break

        # Deduct amount already paid for reservation
        total_price -= sum(flight.price for flight in reservation.flights) * len(
            reservation.passengers
        )

        if safeguard_config.API_CHECK:  # line: 106
            if total_price != payment_amount:
                process_error(
                    (
                        f"The provided payment amount {payment_amount} does not match the computed total price {total_price} for the update."
                    ),
                    ["api_check", "api_redesign"],
                )

        # Create payment
        payment = _payment_for_update(user, payment_id, total_price)
        if payment is not None:
            reservation.payment_history.append(payment)

        # Update reservation
        reservation.flights = reservation_flights
        reservation.cabin = cabin  # This was missing from original TauBench

        return reservation

else:

    def update_reservation_flights(
        reservation_id: Annotated[str, "The reservation ID, such as 'ZFA04Y'."],
        cabin: Annotated[CabinClass, "The cabin class of the reservation"],
        flights: Annotated[
            List[FlightInfo | dict],
            "An array of objects containing details about each piece of flight in the ENTIRE new reservation. Even if the a flight segment is not changed, it should still be included in the array.",
        ],
        payment_id: Annotated[
            str,
            "The payment id stored in user profile, such as 'credit_card_7815826', 'gift_card_7815826', 'certificate_7815826'.",
        ],
    ) -> Reservation:
        """
        Update the flight information of a reservation.

        Returns:
            The updated reservation.

        Raises:
            ValueError: If the reservation is not found.
            ValueError: If the user is not found.
            ValueError: If the payment method is not found.
            ValueError: If the certificate cannot be used to update reservation.
            ValueError: If the gift card balance is not enough.
        """
        if all(isinstance(flight, dict) for flight in flights):
            flights = [FlightInfo(**flight) for flight in flights]

        if safeguard_config.API_CHECK and len(flights) == 0:  # line: 111
            process_error("Flights list cannot be empty", ["api_check"])
        reservation = _get_reservation(reservation_id)
        user = _get_user(reservation.user_id)

        if safeguard_config.API_CHECK and cabin != reservation.cabin:  # line: 116
            # check if flight have already been flown
            for reservation_flight in reservation.flights:
                flight_date_data = _get_flight_instance(
                    flight_number=reservation_flight.flight_number,
                    date=reservation_flight.date,
                )
                if isinstance(flight_date_data, FlightDateStatusLanded) or isinstance(
                    flight_date_data, FlightDataStatusFlying
                ):
                    process_error(
                        (
                            "Cannot change cabin class for already flown flights. "
                            f"Flight {reservation_flight.flight_number} on date {reservation_flight.date} has already been flown."
                        ),
                        ["api_check"],
                    )

        # update flights and calculate price
        total_price = 0
        reservation_flights = []
        change_flights = False
        for flight_info in flights:
            # if existing flight, keep it
            matching_reservation_flight = next(
                (
                    reservation_flight
                    for reservation_flight in reservation.flights
                    if reservation_flight.flight_number == flight_info.flight_number
                    and reservation_flight.date == flight_info.date
                    and cabin == reservation.cabin
                ),
                None,
            )
            if matching_reservation_flight:
                total_price += matching_reservation_flight.price * len(
                    reservation.passengers
                )
                reservation_flights.append(matching_reservation_flight)
                continue

            matching_reservation_except_cabin = next(
                (
                    reservation_flight
                    for reservation_flight in reservation.flights
                    if reservation_flight.flight_number == flight_info.flight_number
                    and reservation_flight.date == flight_info.date
                ),
                None,
            )

            if not matching_reservation_except_cabin:
                change_flights = True

            # If new flight:
            flight = _get_flight(flight_info.flight_number)
            # Check flight availability
            flight_date_data = _get_flight_instance(
                flight_number=flight_info.flight_number,
                date=flight_info.date,
            )
            if not isinstance(flight_date_data, FlightDateStatusAvailable):
                process_error(
                    f"Flight {flight_info.flight_number} not available on date {flight_info.date}",
                    ["implemented"],
                )

            # Check seat availability
            if flight_date_data.available_seats[cabin] < len(reservation.passengers):
                process_error(
                    f"Not enough seats on flight {flight_info.flight_number}",
                    ["implemented"],
                )

            # Calculate price and add to reservation
            reservation_flight = ReservationFlight(
                flight_number=flight_info.flight_number,
                date=flight_info.date,
                price=flight_date_data.prices[cabin],
                origin=flight.origin,
                destination=flight.destination,
            )
            total_price += reservation_flight.price * len(reservation.passengers)
            reservation_flights.append(reservation_flight)

        if safeguard_config.API_CHECK:  # line: 111
            if reservation.origin != reservation_flights[0].origin:
                process_error(
                    f"The reservation origin {reservation.origin} does not match the first flight's origin {reservation_flights[0].origin}",
                    ["api_check"],
                )
            if (
                reservation.flight_type == "one_way"
                and reservation.destination != reservation_flights[-1].destination
            ):
                process_error(
                    (
                        "As a one-way flight, destination must match the last flight's destination. "
                        f"The last flight's destination is {reservation_flights[-1].destination}, but the reservation destination is {reservation.destination}."
                    ),
                    ["api_check"],
                )
            if (
                reservation.flight_type == "round_trip"
                and reservation.origin != reservation_flights[-1].destination
            ):
                process_error(
                    (
                        "As a round-trip flight, origin must match the last flight's destination. "
                        f"The last flight's destination is {reservation_flights[-1].destination}, but the reservation origin is {reservation.origin}."
                    ),
                    ["api_check"],
                )
            if reservation.flight_type == "round_trip":
                has_flight_end_at_destination = False
                has_flight_start_at_destination = False
                ori_dst_list = []
                for res_flight in reservation_flights:
                    if res_flight.destination == reservation.destination:
                        has_flight_end_at_destination = True
                    if res_flight.origin == reservation.destination:
                        has_flight_start_at_destination = True
                    ori_dst_list.append((res_flight.origin, res_flight.destination))
                if not (
                    has_flight_end_at_destination and has_flight_start_at_destination
                ):
                    process_error(
                        (
                            "Round trip reservation must have flights that go to and return from the destination. "
                            f" The reservation destination is {reservation.destination}. The current origin-destination pairs are: {ori_dst_list}."
                        ),
                        ["api_check"],
                    )

        if (
            safeguard_config.API_CHECK
            and change_flights
            and reservation.cabin == "basic_economy"
        ):  # line: 110
            process_error(
                "Cannot change flights when cabin class is basic_economy", ["api_check"]
            )

        # Deduct amount already paid for reservation
        total_price -= sum(flight.price for flight in reservation.flights) * len(
            reservation.passengers
        )

        # Create payment
        payment = _payment_for_update(user, payment_id, total_price)
        if payment is not None:
            reservation.payment_history.append(payment)

        # Update reservation
        reservation.flights = reservation_flights
        reservation.cabin = cabin  # This was missing from original TauBench

        return reservation


if safeguard_config.API_REDESIGN:  # line: 106

    def update_reservation_passengers(
        user_id: Annotated[str, "The ID of the user updating the reservation."],
        reservation_id: Annotated[str, "The reservation ID, such as 'ZFA04Y'."],
        passengers: Annotated[
            List[Passenger | dict],
            "An array of objects containing details about each passenger.",
        ],
    ) -> Reservation:
        """
        Update the passenger information of a reservation.

        Returns:
            The updated reservation.

        Raises:
            ValueError: If the user does not own the reservation.
            ValueError: If the reservation is not found.
            ValueError: If the number of passengers does not match.
        """
        if all(isinstance(passenger, dict) for passenger in passengers):
            passengers = [Passenger(**passenger) for passenger in passengers]
        user = _get_user(user_id)
        reservation = _get_reservation(reservation_id)
        if safeguard_config.API_CHECK and reservation.user_id != user_id:  # line: 106
            process_error(
                "User does not own the reservation", ["api_check", "api_redesign"]
            )
        # LOGGER.info(len(passengers))
        # LOGGER.info(len(reservation.passengers))
        if len(passengers) != len(reservation.passengers):
            process_error(
                f"Number of passengers does not match. The current number of passengers is {len(reservation.passengers)}, while the new number of passengers is {len(passengers)}.",
                ["implemented", "api_redesign"],
            )
        reservation.passengers = deepcopy(passengers)
        return reservation

else:

    def update_reservation_passengers(
        reservation_id: Annotated[str, "The reservation ID, such as 'ZFA04Y'."],
        passengers: Annotated[
            List[Passenger | dict],
            "An array of objects containing details about each passenger.",
        ],
    ) -> Reservation:
        """
        Update the passenger information of a reservation.

        Returns:
            The updated reservation.

        Raises:
            ValueError: If the reservation is not found.
            ValueError: If the number of passengers does not match.
        """
        if all(isinstance(passenger, dict) for passenger in passengers):
            passengers = [Passenger(**passenger) for passenger in passengers]
        reservation = _get_reservation(reservation_id)
        # LOGGER.info(len(passengers))
        # LOGGER.info(len(reservation.passengers))
        if len(passengers) != len(reservation.passengers):
            process_error(
                f"Number of passengers does not match. The current number of passengers is {len(reservation.passengers)}, while the new number of passengers is {len(passengers)}.",
                ["implemented"],
            )
        reservation.passengers = deepcopy(passengers)
        return reservation


def get_flight_status(
    flight_number: Annotated[str, "The flight number."],
    date: Annotated[str, "The date of the flight."],
) -> str:
    """
    Get the status of a flight.

    Returns:
        The status of the flight.

    Raises:
        ValueError: If the flight is not found.
    """
    return _get_flight_instance(flight_number, date).status


def compute_compensation_amount(
    user_id: Annotated[
        str, "The ID of the user to book the reservation, such as 'sara_doe_496'."
    ],
    reservation_id: Annotated[
        str,
        "The reservation ID to associate the certificate with, such as 'ZFA04Y'.",
    ],
    compensation_reason: Annotated[CompensatonReason, "The reason for compensation."],
) -> int:
    """
    Compute the compensation amount for a reservation.

    Returns:
        The compensation amount.
    """

    user = _get_user(user_id)
    reservation = _get_reservation(reservation_id)
    if safeguard_config.API_CHECK:  # line: 106
        if reservation.user_id != user_id:
            process_error("User does not own the reservation", ["api_check", "new_api"])
    if (
        safeguard_config.API_CHECK
        and compensation_reason != "cancellation"
        and compensation_reason != "delay"
    ):
        process_error(
            f"Invalid compensation reason. Valid reasons are 'cancellation' and 'delay', but got '{compensation_reason}'.",
            ["new_api", "api_check"],
        )
    if safeguard_config.API_CHECK:  # line: 157, 161
        if (
            user.membership == "regular"
            and reservation.insurance == "no"
            and reservation.cabin != "business"
        ):
            process_error(
                (
                    "Only users with silver or gold membership, or with insurance, or in business class can receive compensation certificates. "
                    f"User membership: {user.membership}, reservation insurance: {reservation.insurance}, reservation cabin: {reservation.cabin}."
                ),
                ["api_check", "new_api"],
            )

    if (
        safeguard_config.API_REDESIGN
        and safeguard_config.API_CHECK
        and reservation.compensated == True
    ):  # line: unspecified (commonsense)
        process_error(
            "Compensation certificate has already been issued for this reservation.",
            ["api_redesign", "api_check", "new_api"],
        )

    if (
        safeguard_config.API_CHECK and compensation_reason == "cancellation"
    ):  # line: 163
        found_cancelled_flight = False
        for flight in reservation.flights:
            flight_date_data = _get_flight_instance(
                flight_number=flight.flight_number,
                date=flight.date,
            )
            if isinstance(flight_date_data, FlightDateStatusCancelled):
                found_cancelled_flight = True
                break
        if not found_cancelled_flight:
            process_error(
                "Cannot issue cancellation certificate for reservation without any cancelled flights.",
                ["api_check", "new_api"],
            )
    # if safeguard_config.API_REDESIGN:  # line: 165
    #     for flight in reservation.flights:
    #         flight_date_data = _get_flight_instance(
    #             flight_number=flight.flight_number,
    #             date=flight.date,
    #         )
    #         if isinstance(flight_date_data, FlightDateStatusDelayed):
    #             reservation.has_delay_history = True
    #             break
    if (
        safeguard_config.API_REDESIGN
        and safeguard_config.API_CHECK
        and compensation_reason == "delay"
    ):  # line: 165
        if reservation.has_delay_history == None:
            process_error(
                "The flight has not been cancelled or changed. To offer a compensation, the flight has to be either cancelled or changed because of the delay.",
                ["api_redesign", "api_check", "new_api"],
            )
        if reservation.has_delay_history == False:
            process_error(
                "Cannot issue delay certificate for reservation without any delayed flights.",
                ["api_redesign", "api_check", "new_api"],
            )
    if compensation_reason == "cancellation":
        return 100 * len(reservation.passengers)
    elif compensation_reason == "delay":
        return 50 * len(reservation.passengers)
    else:
        return 0


if safeguard_config.API_REDESIGN:  # line: 106, 157, 161

    def send_certificate(
        user_id: Annotated[
            str, "The ID of the user to book the reservation, such as 'sara_doe_496'."
        ],
        reservation_id: Annotated[
            str,
            "The reservation ID to associate the certificate with, such as 'ZFA04Y'.",
        ],
        compensation_reason: Annotated[
            CompensatonReason, "The reason for compensation."
        ],
        amount: Annotated[int, "The amount of the certificate to send."],
    ) -> str:
        """
        Send a certificate to a user. Be careful!

        Returns:
            A message indicating the certificate was sent.

        Raises:
            ValueError: If the user is not found.
        """
        user = _get_user(user_id)
        reservation = _get_reservation(reservation_id)
        if safeguard_config.API_CHECK:  # line: 106
            if reservation.user_id != user_id:
                process_error(
                    "User does not own the reservation", ["api_check", "api_redesign"]
                )
        if (
            safeguard_config.API_CHECK
            and compensation_reason != "cancellation"
            and compensation_reason != "delay"
        ):
            process_error(
                f"Invalid compensation reason. Valid reasons are 'cancellation' and 'delay', but got '{compensation_reason}'.",
                ["api_redesign", "api_check"],
            )
        if safeguard_config.API_CHECK:  # line: 157, 161
            if (
                user.membership == "regular"
                and reservation.insurance == "no"
                and reservation.cabin != "business"
            ):
                process_error(
                    (
                        "Only users with silver or gold membership, or with insurance, or in business class can receive compensation certificates. "
                        f"User membership: {user.membership}, reservation insurance: {reservation.insurance}, reservation cabin: {reservation.cabin}."
                    ),
                    ["api_check", "api_redesign"],
                )

        if (
            safeguard_config.API_REDESIGN and reservation.compensated == True
        ):  # line: unspecified (commonsense)
            process_error(
                "Compensation certificate has already been issued for this reservation.",
                ["api_redesign", "api_check"],
            )

        if (
            safeguard_config.API_CHECK and compensation_reason == "cancellation"
        ):  # line: 163
            found_cancelled_flight = False
            for flight in reservation.flights:
                flight_date_data = _get_flight_instance(
                    flight_number=flight.flight_number,
                    date=flight.date,
                )
                if isinstance(flight_date_data, FlightDateStatusCancelled):
                    found_cancelled_flight = True
                    break
            if not found_cancelled_flight:
                process_error(
                    "Cannot issue cancellation certificate for reservation without any cancelled flights.",
                    ["api_check", "api_redesign"],
                )
        # if safeguard_config.API_REDESIGN:  # line: 165
        #     for flight in reservation.flights:
        #         flight_date_data = _get_flight_instance(
        #             flight_number=flight.flight_number,
        #             date=flight.date,
        #         )
        #         if isinstance(flight_date_data, FlightDateStatusDelayed):
        #             reservation.has_delay_history = True
        #             break
        if (
            safeguard_config.API_REDESIGN and compensation_reason == "delay"
        ):  # line: 165
            if reservation.has_delay_history == None:
                process_error(
                    "The flight has not been cancelled or changed. To offer a compensation, the flight has to be either cancelled or changed because of the delay.",
                    ["api_redesign", "api_check"],
                )
            if reservation.has_delay_history == False:
                process_error(
                    "Cannot issue delay certificate for reservation without any delayed flights.",
                    ["api_redesign", "api_check"],
                )

        if compensation_reason == "cancellation":
            verified_amount = 100 * len(reservation.passengers)
            if safeguard_config.API_CHECK:  # line: 163
                if verified_amount != amount:
                    process_error(
                        f"Invalid certificate amount for cancellation compensation. The amount should be {verified_amount} = 100 * {len(reservation.passengers)}, but got {amount}.",
                        ["api_check", "api_redesign"],
                    )
        elif compensation_reason == "delay":
            verified_amount = 50 * len(reservation.passengers)
            if safeguard_config.API_CHECK:  # line: 165
                if verified_amount != amount:
                    process_error(
                        f"Invalid certificate amount for delay compensation. The amount should be {verified_amount} = 50 * {len(reservation.passengers)}, but got {amount}.",
                        ["api_check", "api_redesign"],
                    )
        else:
            verified_amount = 0
            if safeguard_config.API_CHECK:  # line: 165
                if verified_amount != amount:
                    process_error(
                        f"Invalid certificate amount. The amount should be {verified_amount} for invalid compensation reason, but got {amount}. Valid reasons are 'cancellation' and 'delay'.",
                        ["api_check", "api_redesign"],
                    )
        if safeguard_config.API_REDESIGN:  # line: unspecified
            reservation.compensated = True
        # add a certificate, assume at most 3 cases per task
        for payment_id in [f"certificate_{id}" for id in _get_new_payment_id()]:
            if payment_id not in user.payment_methods:
                new_payment = Certificate(
                    id=payment_id,
                    amount=amount,
                    source="certificate",
                )
                user.payment_methods[payment_id] = new_payment
                return f"Certificate {payment_id} added to user {user_id} with amount {amount}."
        process_error("Too many certificates", ["api_redesign", "implemented"])

else:

    def send_certificate(
        user_id: Annotated[
            str, "The ID of the user to book the reservation, such as 'sara_doe_496'."
        ],
        amount: Annotated[int, "The amount of the certificate to send."],
    ) -> str:
        """
        Send a certificate to a user. Be careful!

        Returns:
            A message indicating the certificate was sent.

        Raises:
            ValueError: If the user is not found.
        """
        user = _get_user(user_id)

        # add a certificate, assume at most 3 cases per task
        for payment_id in [f"certificate_{id}" for id in _get_new_payment_id()]:
            if payment_id not in user.payment_methods:
                new_payment = Certificate(
                    id=payment_id,
                    amount=amount,
                    source="certificate",
                )
                user.payment_methods[payment_id] = new_payment
                return f"Certificate {payment_id} added to user {user_id} with amount {amount}."
        process_error("Too many certificates", ["implemented"])


mcp.tool(fetch_current_time)
mcp.tool(
    book_reservation,
    meta={"require_confirmation": safeguard_config.USER_CONFIRMATION},
)  # line: 7
mcp.tool(calculate, meta={"skip_golden_eval": True})
mcp.tool(
    cancel_reservation,
    meta={"require_confirmation": safeguard_config.USER_CONFIRMATION},
)  # line: 7
mcp.tool(get_reservation_details)
mcp.tool(get_user_details)
mcp.tool(
    list_all_airports,
)
mcp.tool(
    search_direct_flight,
)
mcp.tool(search_onestop_flight)
mcp.tool(send_certificate)
if safeguard_config.ENABLE_THINKING_STEP:
    mcp.tool(think, meta={"skip_golden_eval": True})
if safeguard_config.TOOL_RESPONSE_TEMPLATE:  # line: 15
    mcp.tool(
        transfer_to_human_agents,
        meta={
            "end_conversation": safeguard_config.TOOL_END_CONVERSATION,  # line: 15
            "response_template": "YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON.",
            "skip_golden_eval": True,
        },
    )
else:
    mcp.tool(
        transfer_to_human_agents,
        meta={
            "end_conversation": safeguard_config.TOOL_END_CONVERSATION,  # line: 15
            "skip_golden_eval": True,
        },
    )
mcp.tool(
    update_reservation_baggages,
    meta={"require_confirmation": safeguard_config.USER_CONFIRMATION},
)  # line: 7
mcp.tool(
    update_reservation_flights,
    meta={"require_confirmation": safeguard_config.USER_CONFIRMATION},
)  # line: 7
mcp.tool(
    update_reservation_passengers,
    meta={"require_confirmation": safeguard_config.USER_CONFIRMATION},
)  # line: 7
mcp.tool(get_flight_status)

if safeguard_config.NEW_API:
    mcp.tool(compute_time_difference)  # line: unspecified (new)
    mcp.tool(compute_reservation_price)  # line: unspecified (new)
    mcp.tool(compute_update_reservation_baggages_price)  # line: unspecified (new)
    mcp.tool(compute_update_reservation_flights_price)  # line: unspecified
    mcp.tool(compute_compensation_amount)  # line: unspecified (new)


@mcp.tool(
    meta={
        "disclose_to_model": False,
    }
)
def save_state() -> str:
    """
    Save the current state of the system.

    Returns:
        A message indicating the state was saved.
    """
    db.dump(TMP_DB_PATH)
    return "State saved successfully."
