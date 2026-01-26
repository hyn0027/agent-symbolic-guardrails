from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class Name(BaseModel):
    family: str = Field(description="The family (last) name of the patient.")
    given: List[str] = Field(
        description="A list of given (first and middle) names of the patient."
    )
    use: Optional[str] = Field(
        None, description="The usage context of the name (e.g., official, nickname)."
    )


class Telecom(BaseModel):
    system: str = Field(description="The type of contact (e.g., phone, email).")
    value: str = Field(
        description="The contact detail (e.g., phone number in format XXX-XXX-XXXX, email address)."
    )
    use: Optional[str] = Field(
        None, description="The usage context of the contact (e.g., home, work)."
    )


class Address(BaseModel):
    line: Optional[List[str]] = Field(None, description="Street address lines.")
    city: Optional[str] = Field(None, description="City of the address.")
    state: Optional[str] = Field(None, description="State of the address.")
    postalCode: Optional[str] = Field(None, description="Postal code of the address.")


class Patient(BaseModel):
    id: str = Field(description="The patient's unique Medical Record Number (MRN).")
    name: List[Name] = Field(description="A list of the patient's names.")
    birthDate: str = Field(description="The patient's birthdate in YYYY-MM-DD format.")
    telecom: Optional[List[Telecom]] = Field(
        None, description="A list of the patient's contact details."
    )
    gender: Optional[str] = Field(
        None,
        description="The patient's legal sex (e.g., male, female, other, unknown).",
    )
    address: Optional[List[Address]] = Field(
        None, description="A list of the patient's addresses."
    )
