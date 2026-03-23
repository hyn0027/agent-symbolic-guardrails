# Hazards

1.
    - Original: Duplicate MedicationRequests due to non-idempotent retries and trivial variations: reissuing post_medication_request after timeouts without verifying prior creation or using idempotency keys, and creating multiple active orders that differ only by minor text, resulting in duplicate active orders for the same patient and medication.
    - Decomposed:
      - Duplicate MedicationRequests due to non-idempotent retries and trivial variations: reissuing post_medication_request after timeouts without verifying prior creation or using idempotency keys
        - Included: Policy 6.5
        - Enforceable: true
      - Duplicate MedicationRequests due to non-idempotent retries and trivial variations: creating multiple active orders that differ only by minor text
        - Enforceable: false
2.
    - Original: Incorrect or malformed patient references and identifiers: associating MedicationRequests to the wrong patient, posting MedicationRequest.subject as a non-Patient or malformed Reference, copying requests without updating the patient reference, or calling get_medication_request with improperly encoded patient identifiers.
    - Decomposed:
      - Incorrect or malformed patient references and identifiers: associating MedicationRequests to the wrong patient
        - Included: Policy 2.4
        - Enforceable: true
      - Incorrect or malformed patient references and identifiers: posting MedicationRequest.subject as a non-Patient or malformed Reference
        - Added: Policy 5.11
        - Enforceable: true
      - Incorrect or malformed patient references and identifiers: copying requests without updating the patient reference
        - Included: Policy 2.4
        - Enforceable: true
      - Incorrect or malformed patient references and identifiers: calling get_medication_request with improperly encoded patient identifiers
        - Added: Policy 5.11
        - Enforceable: true
3.
    - Original: Invalid or policy-inappropriate status/intent values: setting MedicationRequest or ServiceRequest status/intent outside allowed value sets or against policy (e.g., disallowed intent values for controlled substances).
    - Decomposed:
      - Invalid or policy-inappropriate status/intent values: setting MedicationRequest or ServiceRequest status/intent outside allowed value sets
        - Added: Tool schema
        - Enforceable: true
      - Invalid or policy-inappropriate status/intent values: setting MedicationRequest or ServiceRequest status/intent against policy (e.g., disallowed intent values for controlled substances).
        - Enforceable: enforceable with specialist and weaker format
4.
    - Original: Incomplete or falsified ordering provenance and context: missing or falsified authoredOn dates, absent requester/prescriber details, lack of Provenance resources or unique provenance identifiers in batch transactions, and missing basedOn links to the originating ServiceRequest.
    - Decomposed:
      - Incomplete or falsified ordering provenance and context: missing or falsified authoredOn dates
        - Included: Policy 5.7
        - Enforceable: true
      - Incomplete or falsified ordering provenance and context: absent requester/prescriber details
        - Enforceable: out of scope
        - Note: the dataset only contains a subset of the FHIR datamodel and does not include any data for Reference(Practitioner); and all `performer` fields for resources are missing. Given this we do not include the `performer` field in our subset datamodel, as there's not way to meaningfullt fill that, and those requester/prescriber details will therefore always be missing.
      - Incomplete or falsified ordering provenance and context: lack of Provenance resources or unique provenance identifiers in batch transactions
        - Enforceable: already implemented
      - Incomplete or falsified ordering provenance and context: missing basedOn links to the originating ServiceRequest
        - Enforceable: out of scope
        - Note: no based on data model
5.
    - Original: Invalid dispense quantity coding or values: using dispenseRequest.quantity without UCUM unit/system or with zero/negative quantities when a positive amount is required.
    - Decomposed:
      - Invalid dispense quantity coding or values: using dispenseRequest.quantity without UCUM unit/system
        - Enforceable: out of scope
        - Note: dispenseRequest is included in the FHIR datamodel, but but not our subset of datamodel
      - Invalid dispense quantity coding or values: using dispenseRequest.quantity with zero/negative quantities when a positive amount is required
        - Enforceable: out of scope
        - Note: dispenseRequest is included in the FHIR datamodel, but but not our subset of datamodel
6.
    - Original: Ambiguous, invalid, or contradictory administration instructions: using “as directed” as the sole instruction, omitting necessary start/stop dates or duration, specifying unsupported timing repetition parameters, or including multiple conflicting routes.
    - Decomposed:
      - Ambiguous, invalid, or contradictory administration instructions: using “as directed” as the sole instruction
        - Enforceable: out of scope
        - Note: we use a subset of the datamodel and the DosageInstruction does not accept text field. So it won't be possible to use “as directed” as the sole instruction
      - Ambiguous, invalid, or contradictory administration instructions: omitting necessary start/stop dates or duration
        - Enforceable: out of scope
        - Note: we use a subset of the datamodel where timing only accepts `coding` field but not `repeat`.
      - Ambiguous, invalid, or contradictory administration instructions: specifying unsupported timing repetition parameters
        - Enforceable: out of scope
        - Note: we use a subset of the datamodel where timing only accepts `coding` field but not `repeat`.
      - Ambiguous, invalid, or contradictory administration instructions: including multiple conflicting routes.
        - Enforceable: enforceable with specialist and weaker format
        - Note: We need to know which routes are conflicting based on domain knowledge to actually enforce it
7.
    - Original: Inappropriate application of emergency/break-glass security labels: creating MedicationRequest resources with meta.security tags that mark emergency access without proper justification or policy controls.
    - Decomposed:
      - Inappropriate application of emergency/break-glass security labels: creating MedicationRequest resources with meta.security tags that mark emergency access without proper justification or policy controls
        - Enforceable: out of scope
        - Note: Field `meta.security` is not enabled in our data model.
8.
    - Original: PHI disclosure through error handling and logs: echoing entire MedicationRequest payloads (including patient data) in error messages or logs.
    - Decomposed:
      - PHI disclosure through error handling and logs: echoing entire MedicationRequest payloads (including patient data) in error messages
        - Enforceable: out of scope
        - Note: We don't report error messages to anyone other than the user that is currently interacting with the system, and given that Policy 2.1-2.3 already enforces the user to authorize their access to all information regarding the patient before doing anything, it is fine (and actually desired) that they see the entire payload
      - PHI disclosure through error handling and logs: echoing entire MedicationRequest payloads (including patient data) in logs
        - Enforceable: out of scope
        - Note: We don't maintain logs in the system, and this is not an agent problem
9.
    - Original: Failure to enforce patient safety and contraindication checks: posting MedicationRequests without checking allergy history or submitting ServiceRequests that conflict with known contraindications (e.g., pharmacologic stress testing in reactive airway disease or high-grade AV block).
    - Decomposed:
      - Failure to enforce patient safety and contraindication checks: posting MedicationRequests without checking allergy history
        - Added: Policy 5.12
        - Enforceable: true
      - Failure to enforce patient safety and contraindication checks: submitting ServiceRequests that conflict with known contraindications (e.g., pharmacologic stress testing in reactive airway disease or high-grade AV block).
        - Enforceable: enforceable with specialist and weaker format
        - Note: We need to know what are considered contradictions
10.
    - Original: Overly generic error handling that obscures root causes: collapsing all non-2xx HTTP responses into a single “server error” label, impeding correct remediation and safe retry strategies.
    - Decomposed:
      - Overly generic error handling that obscures root causes: collapsing all non-2xx HTTP responses into a single “server error” label, impeding correct remediation and safe retry strategies
        - Enforceable: true
        - Note: not a policy, but rather an API design
11.
    - Original: Unsafe clinical order content: Submitting ServiceRequests for high-risk therapies (e.g., high-flow oxygen for chronic hypercapnia) without required safety parameters such as titration limits.
    - Decompose:
      - Unsafe clinical order content: Submitting ServiceRequests for high-risk therapies (e.g., high-flow oxygen for chronic hypercapnia) without required safety parameters such as titration limits
        - Enforceable: enforceable with specialist and weaker format
        - Note: We need to know what are the high-risk therapies and what's their corresponding safety parameters
12.
    - Original: Unmapped or unaudited FHIR actions: Performing FHIR operations outside the instrumented, audited toolchain or without explicit mapping to UI actions, including using uninstrumented HTTP clients or direct requests instead of the provided tools.
    - Decomposed:
      - Unmapped or unaudited FHIR actions: Performing FHIR operations outside the instrumented, audited toolchain or without explicit mapping to UI actions, including using uninstrumented HTTP clients or direct requests instead of the provided tools.
        - Enforceable: true
        - Included: tool schema
13.
    - Original: Irrelevant or excessive free-text PHI in resources: Creating Observation, MedicationRequest, or ServiceRequest payloads with extraneous narrative PHI (e.g., in valueString/comments) or overly large free-text fields unrelated to the clinical purpose.
    - Decompose:
      - Irrelevant or excessive free-text PHI in resources: Creating Observation, MedicationRequest, or ServiceRequest payloads with extraneous narrative PHI (e.g., in valueString/comments) or overly large free-text fields unrelated to the clinical purpose
        - Enforceable: false
14.
    - Original: PHI exposure via UI channels, notifications, or debugging artifacts: Revealing PHI in group chats, system notifications, UI error messages, or displayed/forwarded stack traces and raw FHIR payloads.
    - Decompsoe:
      - PHI exposure via UI channels, notifications, or debugging artifacts: Revealing PHI in group chats
        - Enforceable: out of scope
        - Note: there is no group chats
      - PHI exposure via UI channels, notifications, or debugging artifacts: Revealing PHI in system notifications
        - Enforceable: out of scope
        - Note: there is no sys notification
      - PHI exposure via UI channels, notifications, or debugging artifacts: Revealing PHI in UI error messages
        - Enforceable: out of scope
        - Note: there is no UI error messages
      - PHI exposure via UI channels, notifications, or debugging artifacts: Revealing PHI in displayed/forwarded stack traces and raw FHIR payloads
        - Enforceable: out of scope
        - Note: similar to entry 8
15.
    - Original: Cross-context disclosure or co-mingling: Returning PHI to the wrong tenant or combining data from multiple patients in a single response.
    - Decomposed:
      - Cross-context disclosure or co-mingling: Returning PHI to the wrong tenant
        - Enforceable: out of scope
        - Note: the system simplt have no way to do this
      - Cross-context disclosure or co-mingling: Combining data from multiple patients in a single response
        - Enforceable: true
        - Added: Policy 2.5
16.
    - Original: Improper persistence or reuse of PHI: Storing or reusing PHI in system prompts, agent memory, client-side logs/browser consoles, temporary files, or caches that persist across sessions or users.
    - Decomposed:
      - Improper persistence or reuse of PHI: Storing or reusing PHI in system prompts
        - Enforceable: out of scope
        - Note: we don't have PHI in sys prompt
      - Improper persistence or reuse of PHI: Storing or reusing PHI in agent memory
        - Enforceable: out of scope
        - Note: we don't save anything beyond the current dialogue, and this is discarded after each session
      - Improper persistence or reuse of PHI: Storing or reusing PHI in client-side logs/browser consoles
        - Enforceable: out of scope
        - Note: we don't store those on the client side
      - Improper persistence or reuse of PHI: Storing or reusing PHI in temporary files
        - Enforceable: out of scope
        - Note: we don't store those in tmp files
      - Improper persistence or reuse of PHI: Storing or reusing PHI in caches that persist across sessions or users
        - Enforceable: out of scope
        - Note: we don't cache those
17.
    - Original: Environment/version mismatches causing interoperability issues: Routing requests to the wrong FHIR environment (test vs production) without clear tagging, or posting resources that include extensions from an incompatible FHIR version.
    - Decomposed:
      - Environment/version mismatches causing interoperability issues: Routing requests to the wrong FHIR environment (test vs production) without clear tagging
        - Enforceable: out of scope
        - Note: we only have one env
      - Environment/version mismatches causing interoperability issues: Posting resources that include extensions from an incompatible FHIR version.
        - Enforceable: true
        - Included: tool schema
18.
    - Original: Missing attribution/provenance on writes: Submitting create requests under a shared service account without embedding agent or user attribution/provenance in the resource.
    - Decomposed:
      - Missing attribution/provenance on writes: Submitting create requests under a shared service account without embedding agent or user attribution/provenance in the resource
        - Enforceable: out of scope
        - Note: the dataset does not include any data for Reference(Practitioner); and all `performer` fields for resources are missing. Given this we do not include the `performer` field in our subset datamodel, as there's not way to meaningfullt fill that, and those attribution/provenance will therefore always be missing.
19.
    - Original: Disclosure of specially protected records: Exposing identifiers or URLs that reveal the existence of SUD-tagged or otherwise specially protected records in outputs.
    - Decomposed:
      - Disclosure of specially protected records: Exposing identifiers or URLs that reveal the existence of SUD-tagged or otherwise specially protected records in outputs
        - Enforceable: enforceable with specialist and weaker format
        - Note: we need some matching/patterns to see what is SUG-tagged and what other things are protected
20.
    - Original: Missing required FHIR metadata, such as meta.profile, meta.tag, or meta.security, including failure to meet server capability statements and mandated implementation guides or to include security/data-origin labels.
    - Decomposed:
      - Missing required FHIR metadata, such as meta.profile, meta.tag, or meta.security, including failure to meet server capability statements and mandated implementation guides or to include security/data-origin labels.
        - Enforceable: true
        - Added: tool schema