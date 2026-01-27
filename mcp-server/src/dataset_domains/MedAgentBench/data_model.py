from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

ResourceTypes = Literal[
    "Patient", "Condition", "MedicationRequest", "Observation", "Procedure"
]
GenderTypes = Literal["male", "female", "other", "unknown"]

# Type DateTime format: YYYY-MM-DDThh:mm:ss.sss+zz:zz


class Resource(BaseModel):
    resourceType: str = Field(description="The type of the FHIR resource.")


class MetaData(BaseModel):
    versionId: Optional[str] = Field(
        None, description="The version identifier of the resource."
    )
    lastUpdated: Optional[datetime] = Field(
        None, description="The last updated timestamp of the resource."
    )
    source: Optional[str] = Field(None, description="The source of the resource.")


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


class Coding(BaseModel):
    system: Optional[str] = Field(
        None,
        description="The identification of the code system that defines the meaning of the symbol.",
    )
    code: Optional[str] = Field(
        None, description="A symbol in syntax defined by the system."
    )
    display: Optional[str] = Field(
        None,
        description="A representation of the meaning of the code in the system, following the rules of the system.",
    )


class CodeableConcept(BaseModel):
    coding: Optional[List[Coding]] = Field(
        None, description="A list of codings that define the concept."
    )
    text: Optional[str] = Field(
        None, description="A human language representation of the concept."
    )


class Identifier(BaseModel):
    system: Optional[str] = Field(
        None, description="The namespace for the identifier value."
    )
    value: Optional[str] = Field(None, description="The value of the identifier.")
    use: Optional[str] = Field(
        None,
        description="The usage context of the identifier (e.g., official, secondary).",
    )
    type: Optional[CodeableConcept] = Field(
        None, description="A coded type for the identifier."
    )


class Subject(BaseModel):
    reference: Optional[str] = Field(
        None, description="A reference to another resource."
    )
    identifier: Optional[Identifier] = Field(
        None, description="An identifier for the referenced resource."
    )


class Extension(BaseModel):
    url: str = Field(
        description="The URL that identifies the meaning of the extension."
    )
    valueCodeableConcept: Optional[CodeableConcept] = Field(
        None, description="The value of the extension as a CodeableConcept."
    )


class ValueQuantity(BaseModel):
    value: Optional[float] = Field(
        None, description="The numerical value of the dose quantity."
    )
    unit: Optional[str] = Field(
        None, description="The unit of measurement for the dose quantity."
    )
    system: Optional[str] = Field(
        None, description="The identification of the code system that defines the unit."
    )
    code: Optional[str] = Field(
        None, description="A symbol in syntax defined by the system for the unit."
    )


class DoseAndRate(BaseModel):
    doseQuantity: Optional[ValueQuantity] = Field(
        None, description="The amount of medication to be administered."
    )


class DosageInstruction(BaseModel):
    timing: Optional[CodeableConcept] = Field(
        None, description="The timing schedule for the medication dosage."
    )
    route: Optional[CodeableConcept] = Field(
        None, description="The route of administration for the medication."
    )
    doseAndRate: Optional[List[DoseAndRate]] = Field(
        None, description="A list of dose and rate instructions."
    )


class Patient(Resource):
    id: str = Field(description="The patient's unique Medical Record Number (MRN).")
    meta: Optional[MetaData] = Field(
        None, description="Metadata about the patient resource."
    )
    extension: Optional[List[Extension]] = Field(
        None, description="A list of extensions for additional information."
    )
    identifier: Optional[List[Identifier]] = Field(
        None, description="A list of the patient's identifiers."
    )
    name: List[Name] = Field(description="A list of the patient's names.")
    telecom: Optional[List[Telecom]] = Field(
        None, description="A list of the patient's contact details."
    )
    gender: Optional[GenderTypes] = Field(
        None,
        description="The patient's legal sex (e.g., male, female, other, unknown).",
    )
    birthDate: str = Field(description="The patient's birthdate in YYYY-MM-DD format.")
    address: Optional[List[Address]] = Field(
        None, description="A list of the patient's addresses."
    )


class Condition(Resource):
    id: str = Field(description="The unique identifier for the condition.")
    meta: Optional[MetaData] = Field(
        None, description="Metadata about the condition resource."
    )
    code: CodeableConcept = Field(description="The specific condition or diagnosis.")
    subject: Subject = Field(
        description="The patient or group that the condition record is associated with.",
    )
    onsetDateTime: Optional[datetime] = Field(
        None,
        description="The estimated or actual date and time of the onset of the condition.",
    )
    recordedDate: Optional[datetime] = Field(
        None, description="The date when the condition was first recorded."
    )


class MedicationRequest(Resource):
    id: str = Field(description="The unique identifier for the medication request.")
    meta: Optional[MetaData] = Field(
        None, description="Metadata about the medication request resource."
    )
    status: Optional[str] = Field(
        None,
        description="The status of the medication request (e.g., active, completed).",
    )
    intent: Optional[str] = Field(
        None,
        description="The intent of the medication request (e.g., order, plan).",
    )
    medicationCodeableConcept: CodeableConcept = Field(
        description="The specific medication that is being requested."
    )
    subject: Subject = Field(
        description="The patient or group that the medication request is associated with.",
    )
    authoredOn: Optional[datetime] = Field(
        None, description="The date when the medication request was authored."
    )
    dosageInstruction: Optional[List[DosageInstruction]] = Field(
        None, description="A list of dosage instructions for the medication."
    )


class Procedure(Resource):
    id: str = Field(description="The unique identifier for the procedure.")
    meta: Optional[MetaData] = Field(
        None, description="Metadata about the procedure resource."
    )
    code: CodeableConcept = Field(
        description="The specific procedure that was performed."
    )
    subject: Subject = Field(
        description="The patient or group that the procedure is associated with.",
    )
    performedDateTime: Optional[datetime] = Field(
        None, description="The date and time when the procedure was performed."
    )


class Observation(Resource):
    id: str = Field(description="The unique identifier for the observation.")
    meta: Optional[MetaData] = Field(
        None, description="Metadata about the observation resource."
    )
    status: Optional[str] = Field(
        None,
        description="The status of the observation (e.g., final, amended).",
    )
    category: Optional[List[CodeableConcept]] = Field(
        None, description="A list of categories for the observation."
    )
    code: CodeableConcept = Field(description="The specific observation that was made.")
    subject: Subject = Field(
        description="The patient or group that the observation is associated with.",
    )
    effectiveDateTime: Optional[datetime] = Field(
        None, description="The date and time when the observation was made."
    )
    issued: Optional[datetime] = Field(
        None, description="The date and time when the observation was issued."
    )
    valueQuantity: Optional[ValueQuantity] = Field(
        None, description="The value of the observation as a quantity."
    )
    interpretation: Optional[List[CodeableConcept]] = Field(
        None, description="A list of interpretations of the observation."
    )
