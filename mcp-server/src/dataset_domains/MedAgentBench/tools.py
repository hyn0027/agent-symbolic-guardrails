from mcp_server import mcp
from dataset_domains.MedAgentBench.data_model import (
    Patient,
    Condition,
    Observation,
    MedicationRequest,
    Procedure,
    DateTimeRange,
    LogicList,
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
        "The patient's birthdate in date time format (YYYY-MM-DD), strict match, or inside a range.",
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
        if isinstance(birthdate, str):
            params.append(("birthdate", birthdate))
        elif isinstance(birthdate, datetime):
            params.append(("birthdate", birthdate.strftime("%Y-%m-%d")))
        elif isinstance(birthdate, DateTimeRange):
            if birthdate.start:
                params.append(
                    ("birthdate", f"ge{birthdate.start.strftime('%Y-%m-%d')}")
                )
            if birthdate.end:
                params.append(("birthdate", f"le{birthdate.end.strftime('%Y-%m-%d')}"))
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
    if _count:
        params.append(("_count", str(_count)))
    if _offset:
        params.append(("_offset", str(_offset)))

    print(f"Searching patients with params: {params}")

    response = requests.get(f"{base_api}Patient", params=params)
    response.raise_for_status()
    bundle = response.json()
    res = [
        Patient.model_validate(entry["resource"], extra="forbid")
        for entry in bundle.get("entry", [])
    ]
    return res


def get_condition(
    patient_id: Annotated[
        Optional[str | LogicList[str]],
        "The patient's unique Medical Record Number (MRN).",
    ],
) -> List[Condition]:
    """
    Retrieve conditions associated with a specific patient.

    Returns:
        List[Condition]: A list of Condition objects associated with the patient.

    Raises:
        HTTPError: If the FHIR server returns an error response.
    """
    params = []
    if patient_id:
        params.extend(process_logic_value(patient_id, "subject"))
    params.append(("_count", "1000"))
    response = requests.get(f"{base_api}Condition", params=params)
    response.raise_for_status()
    bundle = response.json()
    res = [
        Condition.model_validate(entry["resource"], extra="forbid")
        for entry in bundle.get("entry", [])
    ]
    return res


mcp.tool(get_patient)
mcp.tool(get_condition)


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
    )
    print(f"Found {len(patients)} patients in total")

    # condition_num = []
    # for patient in patients:
    #     conditions = get_condition(patient_id=patient.id)
    #     condition_num.append(len(conditions))

    # print(
    #     f"Average number of conditions per patient: {sum(condition_num)/len(condition_num)}"
    # )
    # print(f"Max number of conditions for a patient: {max(condition_num)}")
    # print(f"Min number of conditions for a patient: {min(condition_num)}")

    # print patient 0 as json
    patients = get_patient(
        patient_id=None,
        birthdate=None,
        family=None,
        given=None,
        name=LogicList(values=["a"], operator="OR"),
        address=None,
        address_city=None,
        address_postalcode=None,
        address_state=None,
        gender=None,
        telecom=None,
        _count=1000,
        _offset=None,
    )
    print(f'Found {len(patients)} patients with given name "a"')
    patients = get_patient(
        patient_id=None,
        birthdate=None,
        family=None,
        given=None,
        name=LogicList(values=["a", "b"], operator="OR"),
        address=None,
        address_city=None,
        address_postalcode=None,
        address_state=None,
        gender=None,
        telecom=None,
        _count=1000,
        _offset=None,
    )
    # print(patients[0].model_dump_json(indent=2))
    print(f"Found {len(patients)} patients")


# test()
