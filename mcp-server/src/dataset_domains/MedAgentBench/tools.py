from mcp_server import mcp
from dataset_domains.MedAgentBench.data_model import Patient
from typing import Annotated, Optional, List
import requests

base_api = "http://localhost:8080/fhir/"


def get_patient(
    id: Annotated[Optional[str], "The patient's Medical Record Number (MRN)."],
    birthdate: Annotated[
        Optional[str], "The patient's birthdate in YYYY-MM-DD format."
    ],
    family: Annotated[Optional[str], "The patient's family name."],
    given: Annotated[
        Optional[str], "The patient's given name. May include first and middle names."
    ],
    name: Annotated[
        Optional[str],
        "Any part of the patient's name. When discrete name parameters are used, such as 'family' or 'given', this parameter is ignored.",
    ],
    gender: Annotated[Optional[str], "The patient's legal sex."],
    address: Annotated[
        Optional[str],
        "Any part of the patient's address, including street, city, state, and postal code.",
    ],
    address_city: Annotated[Optional[str], "The city of the patient's address."],
    address_postalcode: Annotated[
        Optional[str], "The postal code of the patient's address."
    ],
    address_state: Annotated[Optional[str], "The state of the patient's address."],
    telecom: Annotated[
        Optional[str], "The patient's phone number (XXX-XXX-XXXX) or email address."
    ],
) -> List[Patient]:
    """
    Search for patients in the FHIR server based on various criteria.

    Returns:
        A list of Patient objects matching the search criteria.

    Raises:
        HTTPError: If the FHIR server returns an error response.
    """

    params = {}
    if id:
        params["identifier"] = id
    if birthdate:
        params["birthdate"] = birthdate
    if family:
        params["family"] = family
    if given:
        params["given"] = given
    if name:
        params["name"] = name
    if gender:
        params["gender"] = gender
    if address:
        params["address"] = address
    if address_city:
        params["address-city"] = address_city
    if address_postalcode:
        params["address-postalcode"] = address_postalcode
    if address_state:
        params["address-state"] = address_state
    if telecom:
        params["telecom"] = telecom

    response = requests.get(f"{base_api}Patient", params=params)
    response.raise_for_status()
    bundle = response.json()
    return [
        Patient.model_validate(entry["resource"]) for entry in bundle.get("entry", [])
    ]


mcp.tool(get_patient)
