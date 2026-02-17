from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Literal, TypeVar, Generic, Dict
from datetime import datetime

T = TypeVar("T")
session_MRN: Optional[str] = None


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
    def default_missing_to_none(cls, data) -> Dict:
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
    def default_missing_to_none(cls, data) -> Dict:
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


class MetaData(BaseModel):
    """Metadata about a FHIR resource."""

    versionId: Optional[str] = Field(
        description="The version identifier of the resource."
    )
    lastUpdated: datetime = Field(
        description="The last updated timestamp of the resource."
    )
    source: Optional[str] = Field(description="The source of the resource.")

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data) -> Dict:
        if isinstance(data, dict) and "versionId" not in data:
            data["versionId"] = None
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
    def default_missing_to_none(cls, data) -> Dict:
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
    def default_missing_to_none(cls, data) -> Dict:
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
    def default_missing_to_none(cls, data) -> Dict:
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
    def default_missing_to_none(cls, data) -> Dict:
        if isinstance(data, dict) and "system" not in data:
            data["system"] = None
        if isinstance(data, dict) and "code" not in data:
            data["code"] = None
        if isinstance(data, dict) and "display" not in data:
            data["display"] = None
        return data

    def is_empty(self) -> bool:
        return not (self.system or self.code or self.display)


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
    def default_missing_to_none(cls, data) -> Dict:
        if isinstance(data, dict) and "coding" not in data:
            data["coding"] = None
        if isinstance(data, dict) and "text" not in data:
            data["text"] = None
        return data

    def is_empty(self) -> bool:
        coding_empty = True
        if self.coding:
            for code in self.coding:
                if not code.is_empty():
                    coding_empty = False
                    break
        text_empty = not self.text
        return coding_empty and text_empty

    @classmethod
    def similar(cls, cc1: "CodeableConcept", cc2: "CodeableConcept") -> bool:
        """Determine if two CodeableConcepts are similar based on their coding and text."""
        # Check if coding lists are similar
        if cc1.coding and cc2.coding:
            for code1 in cc1.coding:
                for code2 in cc2.coding:
                    if code1.system == code2.system and code1.code == code2.code:
                        return True
        # Check if text is similar (case-insensitive)
        if cc1.text and cc2.text:
            if cc1.text.strip().lower() == cc2.text.strip().lower():
                return True
        return False


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
    def default_missing_to_none(cls, data) -> Dict:
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
    def default_missing_to_none(cls, data) -> Dict:
        if isinstance(data, dict) and "identifier" not in data:
            data["identifier"] = None
        return data


class Extension(BaseModel):
    """An extension for additional information not part of the basic definition."""

    url: Optional[str] = Field(
        description="The URL that identifies the meaning of the extension."
    )
    valueCodeableConcept: Optional[CodeableConcept] = Field(
        description="The value of the extension as a CodeableConcept."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data) -> Dict:
        if isinstance(data, dict) and "url" not in data:
            data["url"] = None
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
    def default_missing_to_none(cls, data) -> Dict:
        if isinstance(data, dict) and "value" not in data:
            data["value"] = None
        if isinstance(data, dict) and "unit" not in data:
            data["unit"] = None
        if isinstance(data, dict) and "system" not in data:
            data["system"] = None
        if isinstance(data, dict) and "code" not in data:
            data["code"] = None
        return data

    def is_empty(self) -> bool:
        return not (self.value or self.unit or self.system or self.code)

    @classmethod
    def similar(cls, vq1: "ValueQuantity", vq2: "ValueQuantity") -> bool:
        """Determine if two ValueQuantities are similar based on their value and unit."""
        if vq1.value is not None and vq2.value is not None:
            if vq1.value != vq2.value:
                return False
        if vq1.unit and vq2.unit:
            if vq1.unit.strip().lower() != vq2.unit.strip().lower():
                return False
        return True


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
    def default_missing_to_none(cls, data) -> Dict:
        if isinstance(data, dict) and "doseQuantity" not in data:
            data["doseQuantity"] = None
        if isinstance(data, dict) and "rateQuantity" not in data:
            data["rateQuantity"] = None
        return data

    def is_empty(self) -> bool:
        dose_quantity_empty = not self.doseQuantity or self.doseQuantity.is_empty()
        rate_quantity_empty = not self.rateQuantity or self.rateQuantity.is_empty()
        return dose_quantity_empty and rate_quantity_empty


class Timing(BaseModel):
    """The timing schedule for medication dosage."""

    code: Optional[CodeableConcept] = Field(
        description="A code that defines the timing schedule."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data) -> Dict:
        if isinstance(data, dict) and "code" not in data:
            data["code"] = None
        return data

    def is_empty(self) -> bool:
        return not (self.code and not self.code.is_empty())


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
    def default_missing_to_none(cls, data) -> Dict:
        if isinstance(data, dict) and "timing" not in data:
            data["timing"] = None
        if isinstance(data, dict) and "route" not in data:
            data["route"] = None
        if isinstance(data, dict) and "doseAndRate" not in data:
            data["doseAndRate"] = None
        return data

    def is_incomplete(self) -> bool:
        """Check if the dosage instruction is incomplete (i.e., missing all fields)."""
        timing_empty = not self.timing or self.timing.is_empty()
        route_empty = not self.route or self.route.is_empty()
        dose_and_rate_empty = True
        if self.doseAndRate:
            for dr in self.doseAndRate:
                if not dr.is_empty():
                    dose_and_rate_empty = False
                    break
        return timing_empty or route_empty or dose_and_rate_empty


class Note(BaseModel):
    """A note associated with a service request."""

    text: str = Field(description="The text of the note.")


class Resource(BaseModel):
    """A FHIR resource with a type and optional unique identifier."""

    resourceType: str = Field(description="The type of the FHIR resource.")

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data) -> Dict:
        return data


class Patient(Resource):
    """A patient resource representing an individual receiving healthcare."""

    id: str = Field(description="The patient's unique Medical Record Number (MRN).")
    meta: MetaData
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
    note: Optional[List[Note]] = Field(
        description="A list of notes associated with the patient."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data) -> Dict:
        if isinstance(data, dict) and "id" not in data:
            data["id"] = None
        if isinstance(data, dict) and "extension" not in data:
            data["extension"] = None
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
        if isinstance(data, dict) and "note" not in data:
            data["note"] = None
        return data

    def deidentify(self) -> "Patient":
        """De-identify the patient by removing personal identifiers."""
        self.address = None
        self.telecom = None
        return self


class Condition(Resource):
    """A condition resource representing a clinical condition or diagnosis."""

    id: str = Field(description="The unique identifier for the condition.")
    meta: MetaData
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
    note: Optional[List[Note]] = Field(
        description="A list of notes associated with the condition."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data) -> Dict:
        if isinstance(data, dict) and "id" not in data:
            data["id"] = None
        if isinstance(data, dict) and "code" not in data:
            data["code"] = None
        if isinstance(data, dict) and "subject" not in data:
            data["subject"] = None
        if isinstance(data, dict) and "onsetDateTime" not in data:
            data["onsetDateTime"] = None
        if isinstance(data, dict) and "recordedDate" not in data:
            data["recordedDate"] = None
        if isinstance(data, dict) and "note" not in data:
            data["note"] = None
        return data


MedicationRequestStatus = Literal[
    "active",
    "on-hold",
    "ended",
    "stopped",
    "completed",
    "cancelled",
    "entered-in-error",
    "draft",
    "unknown",
]
MedicationRequestIntent = Literal[
    "proposal",
    "plan",
    "order",
    "original-order",
    "reflex-order",
    "filler-order",
    "instance-order",
    "option",
]


class MedicationRequest(Resource):
    """A medication request resource representing a request for medication."""

    id: Optional[str] = Field(
        description="The unique identifier for the medication request."
    )
    meta: MetaData
    status: Optional[MedicationRequestStatus] = Field(
        description="The status of the medication request (e.g., active, completed).",
    )
    intent: Optional[MedicationRequestIntent] = Field(
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
    note: Optional[List[Note]] = Field(
        description="A list of notes associated with the medication request."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data) -> Dict:
        if isinstance(data, dict) and "id" not in data:
            data["id"] = None
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
        if isinstance(data, dict) and "note" not in data:
            data["note"] = None
        return data

    def incomplete_dosage_instructions(self) -> bool:
        """Check if the medication request has no dosage instructions."""
        if not self.dosageInstruction:
            return True
        for instruction in self.dosageInstruction:
            if not instruction.is_incomplete():
                return False
        return True

    def add_dosage_explanation(self, explanation: str) -> None:
        """Add an explanation for missing dosage instructions"""
        if not self.note:
            self.note = []
        self.note.append(Note(text=explanation))

    @classmethod
    def similar(cls, mr1: "MedicationRequest", mr2: "MedicationRequest") -> bool:
        """Determine if two medication requests are similar based on their medication and subject."""
        # Check subject
        if mr1.subject and mr2.subject:
            if mr1.subject.reference != mr2.subject.reference:
                return False
        # check status
        if mr1.status and mr2.status:
            if mr1.status.strip().lower() != mr2.status.strip().lower():
                return False
        # check intent
        if mr1.intent and mr2.intent:
            if mr1.intent.strip().lower() != mr2.intent.strip().lower():
                return False
        # Check medication        if mr1.medicationCodeableConcept and mr2.medicationCodeableConcept:
        if mr1.medicationCodeableConcept and mr2.medicationCodeableConcept:
            if not CodeableConcept.similar(
                mr1.medicationCodeableConcept, mr2.medicationCodeableConcept
            ):
                return False
        return True


class Procedure(Resource):
    id: str = Field(description="The unique identifier for the procedure.")
    meta: MetaData
    code: Optional[CodeableConcept] = Field(
        description="The specific procedure that was performed."
    )
    subject: Optional[Subject] = Field(
        description="The patient or group that the procedure is associated with.",
    )
    performedDateTime: Optional[datetime] = Field(
        description="The date and time when the procedure was performed."
    )
    note: Optional[List[Note]] = Field(
        description="A list of notes associated with the procedure."
    )

    @model_validator(mode="before")
    @classmethod
    def default_missing_to_none(cls, data) -> Dict:
        if isinstance(data, dict) and "id" not in data:
            data["id"] = None
        if isinstance(data, dict) and "performedDateTime" not in data:
            data["performedDateTime"] = None
        if isinstance(data, dict) and "code" not in data:
            data["code"] = None
        if isinstance(data, dict) and "subject" not in data:
            data["subject"] = None
        if isinstance(data, dict) and "note" not in data:
            data["note"] = None
        return data


ObservationStatus = Literal[
    "registered",
    "specimen-in-process",
    "preliminary",
    "final",
    "amended",
    "corrected",
    "appended",
    "cancelled",
    "entered-in-error",
    "unknown",
    "cannot-be-obtained",
]


class Observation(Resource):
    """
    A medical observation made about a patient.
    """

    id: Optional[str] = Field(description="The unique identifier for the observation.")
    meta: MetaData
    status: Optional[ObservationStatus] = Field(
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
    def default_missing_to_none(cls, data) -> Dict:
        if isinstance(data, dict) and "id" not in data:
            data["id"] = None
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

    @classmethod
    def similar(cls, obs1: "Observation", obs2: "Observation") -> bool:
        """Determine if two observations are similar based on their code and category."""
        # patient
        if obs1.subject and obs2.subject:
            if obs1.subject.reference != obs2.subject.reference:
                return False
        # code
        if obs1.code and obs2.code:
            if not CodeableConcept.similar(obs1.code, obs2.code):
                return False
        # category        if obs1.category and obs2.category:
        if obs1.category and obs2.category:
            category_similar = False
            for cat1 in obs1.category:
                for cat2 in obs2.category:
                    if CodeableConcept.similar(cat1, cat2):
                        category_similar = True
                        break
                if category_similar:
                    break
            if not category_similar:
                return False
        # valueQuantity
        if obs1.valueQuantity and obs2.valueQuantity:
            if not ValueQuantity.similar(obs1.valueQuantity, obs2.valueQuantity):
                return False
        # valueString
        if obs1.valueString and obs2.valueString:
            if obs1.valueString.strip().lower() != obs2.valueString.strip().lower():
                return False
        return True


ServiceRequestStatus = Literal[
    "draft",
    "active",
    "on-hold",
    "entered-in-error",
    "ended",
    "completed",
    "revoked",
    "unknown",
]

ServiceRequestIntent = Literal[
    "proposal",
    "solicit-offer",
    "offer-response",
    "plan",
    "directive",
    "order",
    "original-order",
    "reflex-order",
    "filler-order",
    "instance-order",
    "option",
]


class ServiceRequest(Resource):
    id: Optional[str] = Field(
        description="The unique identifier for the service request."
    )
    meta: MetaData
    code: Optional[CodeableConcept] = Field(
        description="The specific service that is being requested, which can include LOINC, SNOMED, CPT, CBV, THL, or Kuntalitto codes.",
    )
    subject: Optional[Subject] = Field(
        description="The patient or group that the service request is associated with.",
    )
    authoredOn: datetime = Field(
        description="The date when the service request was authored."
    )
    status: Optional[ServiceRequestStatus] = Field(
        description="The status of the service request (e.g., active, completed).",
    )
    intent: Optional[ServiceRequestIntent] = Field(
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
    def default_missing_to_none(cls, data) -> Dict:
        if isinstance(data, dict) and "id" not in data:
            data["id"] = None
        if isinstance(data, dict) and "code" not in data:
            data["code"] = None
        if isinstance(data, dict) and "subject" not in data:
            data["subject"] = None
        if isinstance(data, dict) and "note" not in data:
            data["note"] = None
        if isinstance(data, dict) and "occurrenceDateTime" not in data:
            data["occurrenceDateTime"] = None
        return data

    @classmethod
    def similar(cls, sr1: "ServiceRequest", sr2: "ServiceRequest") -> bool:
        """Determine if two service requests are similar based on their code and subject."""
        # patient
        if sr1.subject and sr2.subject:
            if sr1.subject.reference != sr2.subject.reference:
                return False
        # code
        if sr1.code and sr2.code:
            if not CodeableConcept.similar(sr1.code, sr2.code):
                return False
        # status
        if sr1.status and sr2.status:
            if sr1.status.strip().lower() != sr2.status.strip().lower():
                return False
        # intent
        if sr1.intent and sr2.intent:
            if sr1.intent.strip().lower() != sr2.intent.strip().lower():
                return False
        # priority
        if sr1.priority and sr2.priority:
            if sr1.priority.strip().lower() != sr2.priority.strip().lower():
                return False
        return True


posted_observations = []
posted_medication_requests = []
posted_service_requests = []
