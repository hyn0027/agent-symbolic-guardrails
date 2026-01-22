from mcp_server import mcp
from typing import Annotated
import requests

base_api = "http://localhost:8080/fhir/"


# expose the fhir search patient tool
@mcp.tool
def search_patient(id: Annotated[str, "The ID of the patient to search for"]) -> str:
    """
    Search for a patient by ID.
    """

    response = requests.get(f"{base_api}Patient?_id={id}")
    if response.status_code == 200:
        return response.text
    else:
        return f"Error: {response.status_code} - {response.text}"

