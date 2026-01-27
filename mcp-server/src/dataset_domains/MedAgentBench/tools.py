from mcp_server import mcp
from dataset_domains.MedAgentBench.data_model import (
    Patient,
    Condition,
    Observation,
    MedicationRequest,
    Procedure,
    DateTimeRange,
    LogicList,
    ValueRange,
    process_logic_value,
)
from typing import Annotated, Optional, List
from datetime import datetime
import requests

base_api = "http://localhost:8080/fhir/"


def get_patient(
    patient_id: Annotated[
        Optional[str | LogicList[str]], "The patient's Medical Record Number (MRN)."
    ],
    birthdate: Annotated[
        Optional[datetime | DateTimeRange],
        "The patient’s birthdate, either as a single date (YYYY-MM-DD) or as a datetime range (YYYY-MM-DDTHH:MM:SS±HH:MM)",
    ],
    family: Annotated[Optional[str | LogicList[str]], "The patient's family name."],
    given: Annotated[
        Optional[str | LogicList[str]],
        "The patient's given name. May include first and middle names.",
    ],
    name: Annotated[
        Optional[str | LogicList[str]],
        "Any part of the patient's name. When discrete name parameters are used, such as 'family' or 'given', this parameter is ignored.",
    ],
    gender: Annotated[Optional[str | LogicList[str]], "The patient's legal sex."],
    address: Annotated[
        Optional[str | LogicList[str]],
        "Any part of the patient's address, including street, city, state, and postal code.",
    ],
    address_city: Annotated[
        Optional[str | LogicList[str]], "The city of the patient's address."
    ],
    address_postalcode: Annotated[
        Optional[str | LogicList[str]], "The postal code of the patient's address."
    ],
    address_state: Annotated[
        Optional[str | LogicList[str]], "The state of the patient's address."
    ],
    telecom: Annotated[
        Optional[str | LogicList[str]],
        "The patient's phone number (XXX-XXX-XXXX) or email address.",
    ],
    _count: Annotated[int, "Maximum number of results to return."],
    _offset: Annotated[Optional[int], "Number of results to skip."],
    _sort: Annotated[Optional[str], "Sort the results by a specific field."],
) -> List[Patient]:
    """
    Search for patients in the FHIR server based on various criteria.

    Returns:
        A list of Patient objects matching the search criteria.

    Raises:
        HTTPError: If the FHIR server returns an error response.
    """
    params = []
    if patient_id:
        params.extend(process_logic_value(patient_id, "identifier"))
    if birthdate:
        if isinstance(birthdate, datetime):
            params.append(("birthdate", birthdate.strftime("%Y-%m-%d")))
        elif isinstance(birthdate, DateTimeRange):
            params.extend(birthdate.to_query_params("birthdate"))
    if family:
        params.extend(process_logic_value(family, "family"))
    if given:
        params.extend(process_logic_value(given, "given"))
    if name:
        params.extend(process_logic_value(name, "name"))
    if gender:
        params.extend(process_logic_value(gender, "gender"))
    if address:
        params.extend(process_logic_value(address, "address"))
    if address_city:
        params.extend(process_logic_value(address_city, "address-city"))
    if address_postalcode:
        params.extend(process_logic_value(address_postalcode, "address-postalcode"))
    if address_state:
        params.extend(process_logic_value(address_state, "address-state"))
    if telecom:
        params.extend(process_logic_value(telecom, "telecom"))
    params.append(("_count", str(_count)))
    if _offset:
        params.append(("_offset", str(_offset)))
    if _sort:
        params.append(("_sort", _sort))

    response = requests.get(f"{base_api}Patient", params=params)
    response.raise_for_status()
    bundle = response.json()
    res = [
        Patient.model_validate(entry["resource"], extra="forbid")
        for entry in bundle.get("entry", [])
    ]
    return res


def get_condition(
    condition_id: Annotated[
        Optional[str | LogicList[str]], "The unique identifier of the condition."
    ],
    patient_id: Annotated[
        Optional[str | LogicList[str]],
        "The patient's unique Medical Record Number (MRN).",
    ],
    code: Annotated[
        Optional[str | LogicList[str]], "The icd-10 code of the condition."
    ],
    onset_date: Annotated[
        Optional[datetime | DateTimeRange],
        "The date when the condition began, in date time format (YYYY-MM-DDTHH:MM:SS±HH:MM). Can be a specific date or a range.",
    ],
    recorded_date: Annotated[
        Optional[datetime | DateTimeRange],
        "The date when the condition was recorded, in date time format (YYYY-MM-DDTHH:MM:SS±HH:MM). Can be a specific date or a range.",
    ],
    _count: Annotated[int, "Maximum number of results to return."],
    _offset: Annotated[Optional[int], "Number of results to skip."],
    _sort: Annotated[Optional[str], "Sort the results by a specific field."],
) -> List[Condition]:
    """
    Retrieve conditions associated with a specific patient.

    Returns:
        List[Condition]: A list of Condition objects associated with the patient.

    Raises:
        HTTPError: If the FHIR server returns an error response.
    """
    params = []
    if condition_id:
        params.extend(process_logic_value(condition_id, "_id"))
    if patient_id:
        params.extend(process_logic_value(patient_id, "subject"))
    if code:
        params.extend(process_logic_value(code, "code"))
    if onset_date:
        if isinstance(onset_date, datetime):
            params.append(("onset-date", onset_date.strftime("%Y-%m-%dT%H:%M:%S%z")))
        elif isinstance(onset_date, DateTimeRange):
            params.extend(onset_date.to_query_params("onset-date"))
    if recorded_date:
        if isinstance(recorded_date, datetime):
            params.append(
                ("recorded-date", recorded_date.strftime("%Y-%m-%dT%H:%M:%S%z"))
            )
        elif isinstance(recorded_date, DateTimeRange):
            params.extend(recorded_date.to_query_params("recorded-date"))
    params.append(("_count", str(_count)))
    if _offset:
        params.append(("_offset", str(_offset)))
    if _sort:
        params.append(("_sort", _sort))
    response = requests.get(f"{base_api}Condition", params=params)
    response.raise_for_status()
    bundle = response.json()
    res = [
        Condition.model_validate(entry["resource"], extra="forbid")
        for entry in bundle.get("entry", [])
    ]
    return res


def get_observation(
    observation_id: Annotated[
        Optional[str | LogicList[str]], "The unique identifier of the observation."
    ],
    patient_id: Annotated[
        Optional[str | LogicList[str]],
        "The patient's unique Medical Record Number (MRN).",
    ],
    status: Annotated[
        Optional[str | LogicList[str]],
        "The status of the observation (e.g., final, amended).",
    ],
    category: Annotated[
        Optional[str | LogicList[str]],
        "The category of the observation. Can be 'vital-signs', or 'laboratory'.",
    ],
    code: Annotated[Optional[str | LogicList[str]], "The code of the observation."],
    effective_date: Annotated[
        Optional[datetime | DateTimeRange],
        "The date when the observation was made, in date time format (YYYY-MM-DDTHH:MM:SS±HH:MM). Can be a specific date or a range.",
    ],
    value_string: Annotated[
        Optional[str | LogicList[str]], "The value of the observation as a string."
    ],
    value_quantity: Annotated[
        Optional[float | ValueRange],
        "The value of the observation as a quantity.",
    ],
    _count: Annotated[int, "Maximum number of results to return."],
    _offset: Annotated[Optional[int], "Number of results to skip."],
    _sort: Annotated[Optional[str], "Sort the results by a specific field."],
) -> List[Observation]:
    """
    Retrieve observations from the FHIR server.

    Returns:
        List[Observation]: A list of Observation objects.

    Raises:
        HTTPError: If the FHIR server returns an error response.
    """
    params = []
    params.append(("_count", str(_count)))
    if observation_id:
        params.extend(process_logic_value(observation_id, "_id"))
    if patient_id:
        params.extend(process_logic_value(patient_id, "subject"))
    if status:
        params.extend(process_logic_value(status, "status"))
    if category:
        params.extend(process_logic_value(category, "category"))
    if code:
        params.extend(process_logic_value(code, "code"))
    if effective_date:
        if isinstance(effective_date, datetime):
            params.append(("date", effective_date.strftime("%Y-%m-%dT%H:%M:%S%z")))
        elif isinstance(effective_date, DateTimeRange):
            params.extend(effective_date.to_query_params("date"))
    if value_string:
        params.extend(process_logic_value(value_string, "value-string"))
    if value_quantity:
        if isinstance(value_quantity, float):
            params.append(("value-quantity", str(value_quantity)))
        elif isinstance(value_quantity, ValueRange):
            params.extend(value_quantity.to_query_params("value-quantity"))
    if _offset:
        params.append(("_offset", str(_offset)))
    if _sort:
        params.append(("_sort", _sort))
    response = requests.get(f"{base_api}Observation", params=params)
    response.raise_for_status()
    bundle = response.json()
    res = [
        Observation.model_validate(entry["resource"], extra="forbid")
        for entry in bundle.get("entry", [])
    ]
    return res


def post_observation(observation: Observation) -> Observation:
    """
    Create a new observation in the FHIR server.

    Returns:
        Observation: The created Observation object.

    Raises:
        HTTPError: If the FHIR server returns an error response.
    """
    payload = observation.model_dump_json(exclude_unset=True)

    response = requests.post(
        f"{base_api}/Observation",
        data=payload,
        headers={"Content-Type": "application/fhir+json"},
    )
    response.raise_for_status()
    created_resource = response.json()
    return Observation.model_validate(created_resource, extra="forbid")


def get_medication_request(
    medication_id: Annotated[
        Optional[str | LogicList[str]],
        "The unique identifier of the medication request.",
    ],
    status: Annotated[
        Optional[str | LogicList[str]], "The status of the medication request."
    ],
    intent: Annotated[
        Optional[str | LogicList[str]], "The intent of the medication request."
    ],
    patient_id: Annotated[
        Optional[str | LogicList[str]],
        "The patient's unique Medical Record Number (MRN).",
    ],
    authored_on: Annotated[
        Optional[datetime | DateTimeRange],
        "The date when the medication request was authored, in date time format (YYYY-MM-DDTHH:MM:SS±HH:MM). Can be a specific date or a range.",
    ],
    _count: Annotated[int, "Maximum number of results to return."],
    _offset: Annotated[Optional[int], "Number of results to skip."],
    _sort: Annotated[Optional[str], "Sort the results by a specific field."],
) -> List[MedicationRequest]:
    """
    Retrieve medication requests from the FHIR server.

    Returns:
        List[MedicationRequest]: A list of MedicationRequest objects.

    Raises:
        HTTPError: If the FHIR server returns an error response.
    """
    params = []
    if medication_id:
        params.extend(process_logic_value(medication_id, "_id"))
    if status:
        params.extend(process_logic_value(status, "status"))
    if intent:
        params.extend(process_logic_value(intent, "intent"))
    if patient_id:
        params.extend(process_logic_value(patient_id, "subject"))
    if authored_on:
        if isinstance(authored_on, datetime):
            params.append(("authoredon", authored_on.strftime("%Y-%m-%dT%H:%M:%S%z")))
        elif isinstance(authored_on, DateTimeRange):
            params.extend(authored_on.to_query_params("authoredon"))
    params.append(("_count", str(_count)))
    if _offset:
        params.append(("_offset", str(_offset)))
    if _sort:
        params.append(("_sort", _sort))
    response = requests.get(f"{base_api}MedicationRequest", params=params)
    response.raise_for_status()
    bundle = response.json()
    res = [
        MedicationRequest.model_validate(entry["resource"], extra="forbid")
        for entry in bundle.get("entry", [])
    ]
    return res


def post_medication_request(medication_request: MedicationRequest) -> MedicationRequest:
    """
    Create a new medication request in the FHIR server.

    Returns:
        MedicationRequest: The created MedicationRequest object.

    Raises:
        HTTPError: If the FHIR server returns an error response.
    """
    payload = medication_request.model_dump_json(exclude_unset=True)

    response = requests.post(
        f"{base_api}/MedicationRequest",
        data=payload,
        headers={"Content-Type": "application/fhir+json"},
    )
    response.raise_for_status()
    created_resource = response.json()
    return MedicationRequest.model_validate(created_resource, extra="forbid")


mcp.tool(get_patient)
mcp.tool(get_condition)
mcp.tool(get_observation)
mcp.tool(post_observation)
mcp.tool(get_medication_request)


def test() -> None:
    patients = get_patient(
        patient_id=None,
        birthdate=None,
        family=None,
        given=None,
        name=None,
        address=None,
        address_city=None,
        address_postalcode=None,
        address_state=None,
        gender=None,
        telecom=None,
        _count=1000,
        _offset=None,
        _sort=None,
    )
    print(f"Found {len(patients)} patients in total")

    conditions = get_condition(
        condition_id=None,
        patient_id=None,
        code=None,
        onset_date=None,
        recorded_date=None,
        _count=1000,
        _offset=None,
        _sort=None,
    )
    print(f"Found {len(conditions)} conditions in total")

    observations = get_observation(
        observation_id=None,
        patient_id=None,
        status=None,
        category=None,
        code=None,
        effective_date=None,
        value_string=None,
        value_quantity=None,
        _count=1000,
        _offset=None,
        _sort=None,
    )
    print(f"Found {len(observations)} observations in total")

    from dataset_domains.MedAgentBench.data_model import (
        Subject,
        CodeableConcept,
        Coding,
        ValueQuantity,
    )

    new_observation = Observation(
        resourceType="Observation",
        subject=Subject(
            reference=f"Patient/{patients[0].id}",
            identifier=patients[0].identifier[0] if patients[0].identifier else None,
        ),
        code=CodeableConcept(
            coding=[
                Coding(
                    system="http://loinc.org",
                    code="29463-7",
                    display="Body Weight",
                )
            ],
            text="Body Weight",
        ),
        valueQuantity=ValueQuantity(
            value=70.0,
            unit="kg",
            system="http://unitsofmeasure.org",
            code="kg",
        ),
        status="final",
        category=[
            CodeableConcept(
                coding=[
                    Coding(
                        system="http://terminology.hl7.org/CodeSystem/observation-category",
                        code="vital-signs",
                        display="Vital Signs",
                    )
                ],
                text="Vital Signs",
            )
        ],
        effectiveDateTime=datetime.now(),
        id=None,
        meta=None,
        issued=None,
        valueString=None,
        interpretation=None,
    )
    created_observation = post_observation(new_observation)
    print(f"Created new observation with ID: {created_observation.id}")

    medication_requests = get_medication_request(
        medication_id=None,
        status=None,
        intent=None,
        patient_id=None,
        authored_on=None,
        _count=1000,
        _offset=None,
        _sort=None,
    )
    print(f"Found {len(medication_requests)} medication requests in total")

    from dataset_domains.MedAgentBench.data_model import (
        DosageInstruction,
        Timing,
        DoseAndRate,
    )

    medication_request = MedicationRequest(
        resourceType="MedicationRequest",
        status="active",
        intent="order",
        medicationCodeableConcept=CodeableConcept(
            coding=None, text="Amoxicillin 500mg Capsule"
        ),
        subject=Subject(
            reference=f"Patient/{patients[0].id}",
            identifier=patients[0].identifier[0] if patients[0].identifier else None,
        ),
        authoredOn=datetime.now(),
        dosageInstruction=[
            DosageInstruction(
                timing=Timing(
                    code=CodeableConcept(coding=None, text="Three times a day")
                ),
                route=CodeableConcept(coding=None, text="Oral"),
                doseAndRate=[
                    DoseAndRate(
                        doseQuantity=ValueQuantity(
                            value=500,
                            unit="mg",
                            system="http://unitsofmeasure.org",
                            code="mg",
                        )
                    )
                ],
            )
        ],
        id=None,
        meta=None,
    )
    created_medication_request = post_medication_request(medication_request)
    print(f"Created new medication request with ID: {created_medication_request.id}")


test()
