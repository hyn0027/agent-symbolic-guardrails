from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Literal, TypeVar, Generic
from datetime import datetime

T = TypeVar("T")


class LogicList(BaseModel, Generic[T]):
    """A list of values combined with a logical operator (AND/OR)."""

    values: List[T] = Field(description="A list of values for logical operations.")
    operator: Literal["AND", "OR"] = Field(
        description="Logical operator to apply between the values."
    )

    def to_query_params(self, field_name: str) -> List[tuple[str, str]]:
        if self.operator == "OR":
            joined_values = ",".join(str(v) for v in self.values)
            return [(field_name, joined_values)]
        elif self.operator == "AND":
            return [(field_name, str(v)) for v in self.values]
        else:
            raise ValueError(f"Unsupported operator: {self.operator}")


class ValueRange(BaseModel):
    """A range of numeric values with optional lower and upper bounds."""

    low: Optional[float] = Field(
        description="The lower bound of the range. (inclusive)"
    )
    high: Optional[float] = Field(
        description="The upper bound of the range. (inclusive)"
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "low" not in data:
            data["low"] = None
        if isinstance(data, dict) and "high" not in data:
            data["high"] = None
        return data

    def to_query_params(self, field_name: str) -> List[tuple[str, str]]:
        params = []
        if self.low is not None:
            params.append((field_name, f"ge{self.low}"))
        if self.high is not None:
            params.append((field_name, f"le{self.high}"))
        return params


def process_logic_value(
    value: T | LogicList[T], field_name: str
) -> List[tuple[str, str]]:
    if isinstance(value, LogicList):
        return value.to_query_params(field_name)
    else:
        return [(field_name, str(value))]


ResourceTypes = Literal[
    "Patient",
    "Condition",
    "MedicationRequest",
    "Observation",
    "Procedure",
    "ServiceRequest",
]
GenderTypes = Literal["male", "female", "other", "unknown"]


class DateTimeRange(BaseModel):
    """A range of date-time values with optional start and end timestamps."""

    start: Optional[datetime] = Field(
        description="The start of the date-time range (inclusive). In format YYYY-MM-DDTHH:MM:SS±HH:MM"
    )
    end: Optional[datetime] = Field(
        description="The end of the date-time range (inclusive). In format YYYY-MM-DDTHH:MM:SS±HH:MM"
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "start" not in data:
            data["start"] = None
        if isinstance(data, dict) and "end" not in data:
            data["end"] = None
        return data

    def to_query_params(self, field_name: str) -> List[tuple[str, str]]:
        params = []
        if self.start:
            params.append(
                (field_name, f"ge{self.start.strftime('%Y-%m-%dT%H:%M:%S%z')}")
            )
        if self.end:
            params.append((field_name, f"le{self.end.strftime('%Y-%m-%dT%H:%M:%S%z')}"))
        return params


class Resource(BaseModel):
    """A FHIR resource with a type and optional unique identifier."""

    resourceType: str = Field(description="The type of the FHIR resource.")
    id: Optional[str] = Field(description="The unique identifier of the resource.")

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "id" not in data:
            data["id"] = None
        return data


class MetaData(BaseModel):
    """Metadata about a FHIR resource."""

    versionId: Optional[str] = Field(
        description="The version identifier of the resource."
    )
    lastUpdated: Optional[datetime] = Field(
        description="The last updated timestamp of the resource."
    )
    source: Optional[str] = Field(description="The source of the resource.")

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "versionId" not in data:
            data["versionId"] = None
        if isinstance(data, dict) and "lastUpdated" not in data:
            data["lastUpdated"] = None
        if isinstance(data, dict) and "source" not in data:
            data["source"] = None
        return data


class Name(BaseModel):
    """A human's name with family, given names, and usage context."""

    family: str = Field(description="The family (last) name of the patient.")
    given: List[str] = Field(
        description="A list of given (first and middle) names of the patient."
    )
    use: Optional[str] = Field(
        description="The usage context of the name (e.g., official, nickname)."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "use" not in data:
            data["use"] = None
        return data


class Telecom(BaseModel):
    """A contact detail for a human, such as a phone number or email address."""

    system: str = Field(description="The type of contact (e.g., phone, email).")
    value: str = Field(
        description="The contact detail (e.g., phone number in format XXX-XXX-XXXX, email address)."
    )
    use: Optional[str] = Field(
        description="The usage context of the contact (e.g., home, work)."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "use" not in data:
            data["use"] = None
        return data


class Address(BaseModel):
    """A physical address with street lines, city, state, and postal code."""

    line: Optional[List[str]] = Field(description="Street address lines.")
    city: Optional[str] = Field(description="City of the address.")
    state: Optional[str] = Field(description="State of the address.")
    postalCode: Optional[str] = Field(description="Postal code of the address.")

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "line" not in data:
            data["line"] = None
        if isinstance(data, dict) and "city" not in data:
            data["city"] = None
        if isinstance(data, dict) and "state" not in data:
            data["state"] = None
        if isinstance(data, dict) and "postalCode" not in data:
            data["postalCode"] = None
        return data


class Coding(BaseModel):
    """A coding that defines a symbol from a code system."""

    system: Optional[str] = Field(
        description="The identification of the code system that defines the meaning of the symbol.",
    )
    code: Optional[str] = Field(description="A symbol in syntax defined by the system.")
    display: Optional[str] = Field(
        description="A representation of the meaning of the code in the system, following the rules of the system.",
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "system" not in data:
            data["system"] = None
        if isinstance(data, dict) and "code" not in data:
            data["code"] = None
        if isinstance(data, dict) and "display" not in data:
            data["display"] = None
        return data


class CodeableConcept(BaseModel):
    """
    A concept that is defined by a list of codings and a human-readable text.
    """

    coding: Optional[List[Coding]] = Field(
        description="A list of codings that define the concept."
    )
    text: Optional[str] = Field(
        description="A human language representation of the concept."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "coding" not in data:
            data["coding"] = None
        if isinstance(data, dict) and "text" not in data:
            data["text"] = None
        return data


class Identifier(BaseModel):
    """An identifier for a resource or subject."""

    system: Optional[str] = Field(description="The namespace for the identifier value.")
    value: Optional[str] = Field(description="The value of the identifier.")
    use: Optional[str] = Field(
        description="The usage context of the identifier (e.g., official, secondary)."
    )
    type: Optional[CodeableConcept] = Field(
        description="A coded type for the identifier."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "system" not in data:
            data["system"] = None
        if isinstance(data, dict) and "value" not in data:
            data["value"] = None
        if isinstance(data, dict) and "use" not in data:
            data["use"] = None
        if isinstance(data, dict) and "type" not in data:
            data["type"] = None
        return data


class Subject(BaseModel):
    """A reference to another resource."""

    reference: str = Field(description="A reference to another resource.")
    identifier: Optional[Identifier] = Field(
        description="An identifier for the referenced resource."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "identifier" not in data:
            data["identifier"] = None
        return data


class Extension(BaseModel):
    """An extension for additional information not part of the basic definition."""

    url: str = Field(
        description="The URL that identifies the meaning of the extension."
    )
    valueCodeableConcept: Optional[CodeableConcept] = Field(
        description="The value of the extension as a CodeableConcept."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "valueCodeableConcept" not in data:
            data["valueCodeableConcept"] = None
        return data


class ValueQuantity(BaseModel):
    """A value represented as a quantity with unit and code."""

    value: Optional[float] = Field(
        description="The numerical value of the dose quantity."
    )
    unit: Optional[str] = Field(
        description="The unit of measurement for the dose quantity."
    )
    system: Optional[str] = Field(
        description="The identification of the code system that defines the unit."
    )
    code: Optional[str] = Field(
        description="A symbol in syntax defined by the system for the unit."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "value" not in data:
            data["value"] = None
        if isinstance(data, dict) and "unit" not in data:
            data["unit"] = None
        if isinstance(data, dict) and "system" not in data:
            data["system"] = None
        if isinstance(data, dict) and "code" not in data:
            data["code"] = None
        return data


class DoseAndRate(BaseModel):
    """A dosage instruction with dose quantity and rate quantity."""

    doseQuantity: Optional[ValueQuantity] = Field(
        description="The amount of medication to be administered."
    )
    rateQuantity: Optional[ValueQuantity] = Field(
        description="The speed at which the medication is to be administered."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "doseQuantity" not in data:
            data["doseQuantity"] = None
        if isinstance(data, dict) and "rateQuantity" not in data:
            data["rateQuantity"] = None
        return data


class Timing(BaseModel):
    """The timing schedule for medication dosage."""

    code: Optional[CodeableConcept] = Field(
        description="A code that defines the timing schedule."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "code" not in data:
            data["code"] = None
        return data


class DosageInstruction(BaseModel):
    """Dosage instructions for medication administration."""

    timing: Optional[Timing] = Field(
        description="The timing schedule for the medication dosage."
    )
    route: Optional[CodeableConcept] = Field(
        description="The route of administration for the medication."
    )
    doseAndRate: Optional[List[DoseAndRate]] = Field(
        description="A list of dose and rate instructions."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "timing" not in data:
            data["timing"] = None
        if isinstance(data, dict) and "route" not in data:
            data["route"] = None
        if isinstance(data, dict) and "doseAndRate" not in data:
            data["doseAndRate"] = None
        return data


class Note(BaseModel):
    """A note associated with a service request."""

    text: str = Field(description="The text of the note.")


class Patient(Resource):
    """A patient resource representing an individual receiving healthcare."""

    id: str = Field(description="The patient's unique Medical Record Number (MRN).")
    meta: Optional[MetaData] = Field(description="Metadata about the patient resource.")
    extension: Optional[List[Extension]] = Field(
        description="A list of extensions for additional information."
    )
    identifier: List[Identifier] = Field(
        description="A list of the patient's identifiers."
    )
    name: List[Name] = Field(description="A list of the patient's names.")
    telecom: Optional[List[Telecom]] = Field(
        description="A list of the patient's contact details."
    )
    gender: Optional[GenderTypes] = Field(
        description="The patient's legal sex (e.g., male, female, other, unknown).",
    )
    birthDate: Optional[datetime] = Field(description="The patient's birthdate.")
    address: Optional[List[Address]] = Field(
        description="A list of the patient's addresses."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "meta" not in data:
            data["meta"] = None
        if isinstance(data, dict) and "extension" not in data:
            data["extension"] = None
        if isinstance(data, dict) and "telecom" not in data:
            data["telecom"] = None
        if isinstance(data, dict) and "gender" not in data:
            data["gender"] = None
        if isinstance(data, dict) and "birthDate" not in data:
            data["birthDate"] = None
        if isinstance(data, dict) and "address" not in data:
            data["address"] = None
        return data


class Condition(Resource):
    """A condition resource representing a clinical condition or diagnosis."""

    id: str = Field(description="The unique identifier for the condition.")
    meta: Optional[MetaData] = Field(
        description="Metadata about the condition resource."
    )
    code: Optional[CodeableConcept] = Field(
        description="The specific condition or diagnosis."
    )
    subject: Optional[Subject] = Field(
        description="The patient or group that the condition record is associated with.",
    )
    onsetDateTime: Optional[datetime] = Field(
        description="The estimated or actual date and time of the onset of the condition.",
    )
    recordedDate: Optional[datetime] = Field(
        description="The date when the condition was first recorded."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "meta" not in data:
            data["meta"] = None
        if isinstance(data, dict) and "code" not in data:
            data["code"] = None
        if isinstance(data, dict) and "subject" not in data:
            data["subject"] = None
        if isinstance(data, dict) and "onsetDateTime" not in data:
            data["onsetDateTime"] = None
        if isinstance(data, dict) and "recordedDate" not in data:
            data["recordedDate"] = None
        return data


class MedicationRequest(Resource):
    """A medication request resource representing a request for medication."""

    id: Optional[str] = Field(
        description="The unique identifier for the medication request."
    )
    meta: Optional[MetaData] = Field(
        description="Metadata about the medication request resource."
    )
    status: Optional[str] = Field(
        description="The status of the medication request (e.g., active, completed).",
    )
    intent: Optional[str] = Field(
        description="The intent of the medication request (e.g., order, plan).",
    )
    medicationCodeableConcept: Optional[CodeableConcept] = Field(
        description="The specific medication that is being requested."
    )
    subject: Optional[Subject] = Field(
        description="The patient or group that the medication request is associated with.",
    )
    authoredOn: Optional[datetime] = Field(
        description="The date when the medication request was authored."
    )
    dosageInstruction: Optional[List[DosageInstruction]] = Field(
        description="A list of dosage instructions for the medication."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "meta" not in data:
            data["meta"] = None
        if isinstance(data, dict) and "status" not in data:
            data["status"] = None
        if isinstance(data, dict) and "intent" not in data:
            data["intent"] = None
        if isinstance(data, dict) and "medicationCodeableConcept" not in data:
            data["medicationCodeableConcept"] = None
        if isinstance(data, dict) and "subject" not in data:
            data["subject"] = None
        if isinstance(data, dict) and "authoredOn" not in data:
            data["authoredOn"] = None
        if isinstance(data, dict) and "dosageInstruction" not in data:
            data["dosageInstruction"] = None
        return data


class Procedure(Resource):
    id: str = Field(description="The unique identifier for the procedure.")
    meta: Optional[MetaData] = Field(
        description="Metadata about the procedure resource."
    )
    code: Optional[CodeableConcept] = Field(
        description="The specific procedure that was performed."
    )
    subject: Optional[Subject] = Field(
        description="The patient or group that the procedure is associated with.",
    )
    performedDateTime: Optional[datetime] = Field(
        description="The date and time when the procedure was performed."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "meta" not in data:
            data["meta"] = None
        if isinstance(data, dict) and "performedDateTime" not in data:
            data["performedDateTime"] = None
        if isinstance(data, dict) and "code" not in data:
            data["code"] = None
        if isinstance(data, dict) and "subject" not in data:
            data["subject"] = None
        return data


class Observation(Resource):
    """
    A medical observation made about a patient.
    """

    id: Optional[str] = Field(description="The unique identifier for the observation.")
    meta: Optional[MetaData] = Field(
        description="Metadata about the observation resource."
    )
    status: Optional[str] = Field(
        description="The status of the observation (e.g., final, amended).",
    )
    category: Optional[List[CodeableConcept]] = Field(
        description="A list of categories for the observation."
    )
    code: Optional[CodeableConcept] = Field(
        description="The specific observation that was made."
    )
    subject: Optional[Subject] = Field(
        description="The patient or group that the observation is associated with.",
    )
    effectiveDateTime: Optional[datetime] = Field(
        description="The date and time when the observation was made."
    )
    issued: Optional[datetime] = Field(
        description="The date and time when the observation was issued."
    )
    valueQuantity: Optional[ValueQuantity] = Field(
        description="The value of the observation as a quantity."
    )
    interpretation: Optional[List[CodeableConcept]] = Field(
        description="A list of interpretations of the observation."
    )
    valueString: Optional[str] = Field(
        description="The value of the observation as a string."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "meta" not in data:
            data["meta"] = None
        if isinstance(data, dict) and "status" not in data:
            data["status"] = None
        if isinstance(data, dict) and "category" not in data:
            data["category"] = None
        if isinstance(data, dict) and "code" not in data:
            data["code"] = None
        if isinstance(data, dict) and "subject" not in data:
            data["subject"] = None
        if isinstance(data, dict) and "effectiveDateTime" not in data:
            data["effectiveDateTime"] = None
        if isinstance(data, dict) and "issued" not in data:
            data["issued"] = None
        if isinstance(data, dict) and "valueQuantity" not in data:
            data["valueQuantity"] = None
        if isinstance(data, dict) and "interpretation" not in data:
            data["interpretation"] = None
        if isinstance(data, dict) and "valueString" not in data:
            data["valueString"] = None
        return data


class ServiceRequest(Resource):
    id: Optional[str] = Field(
        description="The unique identifier for the service request."
    )
    meta: Optional[MetaData] = Field(
        description="Metadata about the service request resource."
    )
    code: Optional[CodeableConcept] = Field(
        description="The specific service that is being requested, which can include LOINC, SNOMED, CPT, CBV, THL, or Kuntalitto codes.",
    )
    subject: Optional[Subject] = Field(
        description="The patient or group that the service request is associated with.",
    )
    authoredOn: datetime = Field(
        description="The date when the service request was authored."
    )
    status: str = Field(
        description="The status of the service request (e.g., active, completed).",
    )
    intent: str = Field(
        description="The intent of the service request (e.g., order, plan).",
    )
    priority: str = Field(
        description="The priority of the service request (e.g., routine, urgent).",
    )
    note: Optional[List[Note]] = Field(
        description="A list of notes associated with the service request."
    )
    occurrenceDateTime: Optional[datetime] = Field(
        description="The date and time when the service is to occur."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data):
        if isinstance(data, dict) and "meta" not in data:
            data["meta"] = None
        if isinstance(data, dict) and "code" not in data:
            data["code"] = None
        if isinstance(data, dict) and "subject" not in data:
            data["subject"] = None
        if isinstance(data, dict) and "note" not in data:
            data["note"] = None
        if isinstance(data, dict) and "occurrenceDateTime" not in data:
            data["occurrenceDateTime"] = None
        return data
