# MedAgentBench API Endpoints

Base URL: `http://localhost:8080/fhir/`

Current time: 2023-11-13T10:15:00+00:00

## Read endpoints

### `GET /Patient`: search for patients

Searches patient records and returns demographic information for each match. No parameter is required.

- `name`: any part of the patient's name (ignored if `given` or `family` is used)
- `given`, `family`: first/middle name, last name
- `birthdate`: date of birth (YYYY-MM-DD)
- `identifier`: patient identifier (e.g., MRN)
- `gender` / `legal-sex`: legal sex (`legal-sex` takes precedence)
- `address`, `address-city`, `address-state`, `address-postalcode`: home address
- `telecom`: phone number or email

### `GET /Condition`: get the problem list

Returns the conditions on a patient's problem list across all encounters. Medical history recorded outside the problem list is not included.

- `patient` (required): patient FHIR ID
- `category`: always `problem-list-item`

### `GET /Observation`: get lab results

Returns component-level lab results.

- `patient` (required): patient FHIR ID
- `code` (required): the lab test identifier
- `date`: when the specimen was obtained

### `GET /Observation`: get vital signs

Returns vital signs and other flowsheet data across all encounters.

- `patient` (required): patient FHIR ID
- `category` (required): `vital-signs`
- `date`: date range of the observation

### `GET /MedicationRequest`: get medication orders

Returns a patient's medication orders, including inpatient, clinic-administered, patient-reported, and externally reconciled medications.

- `patient` (required): patient FHIR ID
- `category`: `Inpatient`, `Outpatient`, `Community` (prescriptions), or `Discharge`; all categories by default
- `date`: medication administration date (filtering by date may hide active medications)

### `GET /Procedure`: get completed procedures

Returns completed procedures performed on the patient (e.g., surgeries, endoscopies, counseling).

- `patient` (required): patient FHIR ID
- `date` (required): date or period the procedure was performed
- `code`: CPT code

## Write endpoints

### `POST /Observation`: record a vital sign

Files a vital sign (or other flowsheet value) to the patient's chart.

- `resourceType` (required): `Observation`
- `category` (required): `coding` with system `http://hl7.org/fhir/observation-category`, code `vital-signs`, display `Vital Signs`
- `code.text` (required): what is measured (flowsheet ID or LOINC mapping)
- `valueString` (required): the measured value
- `effectiveDateTime` (required): when the measurement was taken (ISO format)
- `status` (required): `final` (non-final data cannot be filed)
- `subject.reference` (required): the patient (`Patient/{id}`)

### `POST /MedicationRequest`: order a medication

Creates a new medication order for the patient.

- `resourceType` (required): `MedicationRequest`
- `medicationCodeableConcept` (required): the medication, as `coding` (system such as NDC `http://hl7.org/fhir/sid/ndc`, code, display) plus a `text` display name
- `dosageInstruction` (required): list of instructions, each with
  - `route.text`: administration route
  - `doseAndRate`: `doseQuantity` (value + unit, e.g. `g`) and/or `rateQuantity` (value + unit, e.g. `h`)
- `authoredOn` (required): date the prescription was written
- `status` (required): `active`
- `intent` (required): `order`
- `subject.reference` (required): the patient (`Patient/{id}`)

### `POST /ServiceRequest`: order a service or procedure

Creates a new order for a lab, procedure, or other service.

- `resourceType` (required): `ServiceRequest`
- `code` (required): the service, as `coding` (system such as LOINC `http://loinc.org`, SNOMED, or CPT; code; display)
- `authoredOn` (required): when the order is signed
- `status` (required): `active`
- `intent` (required): `order`
- `priority` (required): `stat`
- `subject.reference` (required): the patient (`Patient/{id}`)
- `occurrenceDateTime`: when the service should be performed (ISO format)
- `note.text`: free-text comment
