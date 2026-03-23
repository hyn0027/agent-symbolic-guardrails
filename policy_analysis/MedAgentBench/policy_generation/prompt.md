## Your task
Generate a comprehensive safety policy governing an LLM-powered agent’s behavior.

## Details about the agent
- The agent is designed to assist users (healthcare providers) in interacting with a FHIR-compliant Electronic Medical Record (EMR) system
- The agent interacts with users only via text 
- The agent is equipped with a defined set of tools, detailed below, which it can invoke as needed
- The agent has no access to external systems and services beyond the explicitly provided tools

## Policy requirements
- Write the policy as bullet points organized under sections
- Each bullet point must state one specific safety requirement
- The requirements should be concise and should not contain duplicate entries
- The requirements should be detailed and concrete
- The requirements should be precise and unambiguous
- Do not include requirements that are already specified in the tool schema
- Address the agent as “you” within each requirement

## Available tools
```
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

def post_observation(observation: Observation) -> Observation:
    """
    Create a new observation in the FHIR server.

    Returns:
        Observation: The created Observation object.

    Raises:
        HTTPError: If the FHIR server returns an error response.
    """

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

def post_medication_request(medication_request: MedicationRequest) -> MedicationRequest:
    """
    Create a new medication request in the FHIR server.

    Returns:
        MedicationRequest: The created MedicationRequest object.

    Raises:
        HTTPError: If the FHIR server returns an error response.
    """

def get_procedure(
    procedure_id: Annotated[
        Optional[str | LogicList[str]], "The unique identifier of the procedure."
    ],
    patient_id: Annotated[
        Optional[str | LogicList[str]],
        "The patient's unique Medical Record Number (MRN).",
    ],
    code: Annotated[
        Optional[str | LogicList[str]],
        "The code of the procedure, following CPT standards.",
    ],
    performed_date_time: Annotated[
        Optional[datetime | DateTimeRange],
        "The date when the procedure was performed, in date time format (YYYY-MM-DDTHH:MM:SS±HH:MM). Can be a specific date or a range.",
    ],
    _count: Annotated[int, "Maximum number of results to return."],
    _offset: Annotated[Optional[int], "Number of results to skip."],
    _sort: Annotated[Optional[str], "Sort the results by a specific field."],
) -> List[Procedure]:
    """
    Retrieve procedures from the FHIR server.

    Returns:
        List[Procedure]: A list of Procedure objects.

    Raises:
        HTTPError: If the FHIR server returns an error response.
    """

def post_service_request(service_request: ServiceRequest) -> ServiceRequest:
    """
    Create a new service request in the FHIR server.

    Returns:
        ServiceRequest: The created ServiceRequest object.
    Raises:
        HTTPError: If the FHIR server returns an error response.
    """
```

## Datamodel references
```
class LogicList(BaseModel, Generic[T]):
    """A list of values combined with a logical operator (AND/OR)."""

    values: List[T] = Field(description="A list of values for logical operations.")
    operator: Literal["AND", "OR"] = Field(
        description="Logical operator to apply between the values."
    )

class ValueRange(BaseModel):
    """A range of numeric values with optional lower and upper bounds."""

    low: Optional[float] = Field(
        description="The lower bound of the range. (inclusive)"
    )
    high: Optional[float] = Field(
        description="The upper bound of the range. (inclusive)"
    )

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

class Resource(BaseModel):
    """A FHIR resource with a type and optional unique identifier."""

    resourceType: str = Field(description="The type of the FHIR resource.")
    id: Optional[str] = Field(description="The unique identifier of the resource.")

class MetaData(BaseModel):
    """Metadata about a FHIR resource."""

    versionId: Optional[str] = Field(
        description="The version identifier of the resource."
    )
    lastUpdated: Optional[datetime] = Field(
        description="The last updated timestamp of the resource."
    )
    source: Optional[str] = Field(description="The source of the resource.")

class Name(BaseModel):
    """A human's name with family, given names, and usage context."""

    family: str = Field(description="The family (last) name of the patient.")
    given: List[str] = Field(
        description="A list of given (first and middle) names of the patient."
    )
    use: Optional[str] = Field(
        description="The usage context of the name (e.g., official, nickname)."
    )

class Telecom(BaseModel):
    """A contact detail for a human, such as a phone number or email address."""

    system: str = Field(description="The type of contact (e.g., phone, email).")
    value: str = Field(
        description="The contact detail (e.g., phone number in format XXX-XXX-XXXX, email address)."
    )
    use: Optional[str] = Field(
        description="The usage context of the contact (e.g., home, work)."
    )

class Address(BaseModel):
    """A physical address with street lines, city, state, and postal code."""

    line: Optional[List[str]] = Field(description="Street address lines.")
    city: Optional[str] = Field(description="City of the address.")
    state: Optional[str] = Field(description="State of the address.")
    postalCode: Optional[str] = Field(description="Postal code of the address.")

class Coding(BaseModel):
    """A coding that defines a symbol from a code system."""

    system: Optional[str] = Field(
        description="The identification of the code system that defines the meaning of the symbol.",
    )
    code: Optional[str] = Field(description="A symbol in syntax defined by the system.")
    display: Optional[str] = Field(
        description="A representation of the meaning of the code in the system, following the rules of the system.",
    )

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

class Subject(BaseModel):
    """A reference to another resource."""

    reference: str = Field(description="A reference to another resource.")
    identifier: Optional[Identifier] = Field(
        description="An identifier for the referenced resource."
    )

class Extension(BaseModel):
    """An extension for additional information not part of the basic definition."""

    url: str = Field(
        description="The URL that identifies the meaning of the extension."
    )
    valueCodeableConcept: Optional[CodeableConcept] = Field(
        description="The value of the extension as a CodeableConcept."
    )

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

class DoseAndRate(BaseModel):
    """A dosage instruction with dose quantity and rate quantity."""

    doseQuantity: Optional[ValueQuantity] = Field(
        description="The amount of medication to be administered."
    )
    rateQuantity: Optional[ValueQuantity] = Field(
        description="The speed at which the medication is to be administered."
    )

class Timing(BaseModel):
    """The timing schedule for medication dosage."""

    code: Optional[CodeableConcept] = Field(
        description="A code that defines the timing schedule."
    )

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
```