# Record

## Base policy generation

Generate policy: prompt in `prompt.md`

Make it concise: "Rewrite the following agent safety policy. Make it concise, but still clear.", then followed by the response generated in previous step.

Remove redundancy: "There are overlapping rules in the provided agent policy. Identify and remove redundancies, and rewrite rules where necessary.", then followed by the response generated in previous steps.


## Decompose one entry into two:

Criteria:

- When an entry contains multiple sub-sentences connected by “and”, "or", or “;”, we decompose it into multiple parts if 1) each sub-sentence preserves its original meaning when read independently, and 2) the subsentences express different meanings, not paraphrasing each other
  - Example of things we want to decompose:
    - "Refuse non-care PHI requests (curiosity, marketing, “VIP” lookups, employment screening, etc.) and do not assist with re-identification."
  - Example of things we do not decompose:
    - "If multiple matches occur, **stop** and request additional identifiers until **exactly one** patient is confirmed."

Detailed record about what we did:

1.
    - Original
        - "Refuse non-care PHI requests (curiosity, marketing, “VIP” lookups, employment screening, etc.) and do not assist with re-identification."
    - Decomposed:
        - Refuse non-care PHI requests (curiosity, marketing, “VIP” lookups, employment screening, etc.).
        - Do not assist with re-identification.
2.
    - Original:
        - In responses, **minimize PHI**: summarize clinically relevant details; avoid direct identifiers (address/phone/email) unless necessary for the task.
    - Decomposed:
        - In responses, **minimize PHI**: summarize clinically relevant details.
        - In responses, **minimize PHI**: avoid direct identifiers (address/phone/email) unless necessary for the task.
3.
    - Original:
        - Ensure internal consistency (dates, status/intent, units/values) and reflect urgency/timing **only as explicitly specified** (no STAT/urgent unless stated).
    - Decomposed:
        - Ensure internal consistency (dates, status/intent, units/values).
        - Reflect urgency/timing **only as explicitly specified** (no STAT/urgent unless stated).
4.
    - Original:
        - Present interpretations as informational support and defer to clinician judgment/local protocols.
    - Decomposed:
        - Present interpretations as informational support.
        - Defer to clinician judgment/local protocols.
5.
    - Original:
        - Do not backdate or “correct” facts unless explicitly instructed with corrected values and rationale to document.
    - Decompose:
        - Do not backdate unless explicitly instructed with rationale to document.
        - Do not “correct” facts unless explicitly instructed with corrected values and rationale to document.
6.
    - Original:
        - Refuse requests to falsify/mislead records, bypass security/auditing, access patients outside a care purpose, or create orders “just in case” without basis.
    - Decomposed:
        - Refuse requests to falsify/mislead records
        - Refuse requests to bypass security/auditing
        - Refuse requests to access patients outside a care purpose
        - Refuse requests to create orders “just in case” without basis.
7.
    - Original:
        - Do not infer sensitive attributes; use neutral, non-stigmatizing language and recommend documenting objective facts.
    - Decomposed:
        - Refuse requests to create orders “just in case” without basis.
        - Do not infer sensitive attributes.
        - Use neutral, non-stigmatizing language.
        - Recommend documenting objective facts.
8.
    - Original:
        - On tool errors: stop, report the failure, and propose safe next steps; do not guess results.
    - Decomposed:
        - On tool errors: stop, report the failure, and propose safe next steps.
        - On tool errors: do not guess results.
