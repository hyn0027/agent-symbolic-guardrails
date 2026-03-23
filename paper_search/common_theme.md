# Common Themes

## 1. Privacy leakage and confidentiality

- private data leakage
- PrivacyLeakage
- privacy
- confidentiality
- confidentiality-aware guidelines
- do not reveal private or sensitive data that are irrelevant to the task
- obtaining personal data
- information leakage
- leaking private model data

## 2. Unauthorized actions and privilege abuse

- UA (UnauthorizedAction)
- unsafe or unauthorized tool actions
- privilege bypass
- fraudulent approvals
- agent should not modify user state
- only perform actions aligned with the instruction

## 3. Prompt injection defense

- prompt injection
- direct and indirect prompt injection
- malicious party may attempt to hijack the objective
- adversarial instructions on webpages
- web agent should resist prompt injection attacks that try to change its task

## 4. Tool misuse prevention

- tool execution only when absolutely necessary
- avoid mistaken tool calls
- avoid calling tools before obtaining complete information
- ignore no known constraints when calling tools
- use correct parameters when calling tools
- suspicious tool call patterns

## 5. Data minimization and least privilege

- strict data minimization
- minimum required portion of data
- necessity assessment before tool execution
- atomized perspective
- no synthesis of privacy fragments into sensitive conclusions
- boundary, strict execution

## 6. Secure code generation

- coding agent should generate secure code
- safe code generation
- should not generate or execute malicious code
- risky code, security, ethical
- coding agent should defend against attacks injected in code or prompt

## 7. Code injection and software vulnerabilities

- CWE-77 Command Injection
- CWE-20 Improper Input Validation
- CWE-89 SQL Injection
- CWE-94 Code Injection
- CWE-22 Path Traversal
- CWE-79 XSS
- CWE-200 Exposure of Sensitive Information
- CWE-434 Unrestricted Upload of Dangerous File Types

## 8. Computer security compromise

- compromising computer processes
- gaining remote control permissions
- accessing passwords, tokens, private keys, credentials
- system security compromise
- malware generation and execution

## 9. Phishing, scams, and deceptive interfaces

- Phishing Web
- Phishing Email
- Account Fraud
- deceptive website design
- pop-ups and ads
- reCAPTCHA traps

## 10. Unsafe links and malicious UI interactions

- mobile phone agents should not click unsafe links
- web agent should not click malicious popups
- spam popup detection
- induced text on webpages
- suspicious website elements

## 11. Memory poisoning and persistent compromise

- memory poisoning
- persistent harmful influence across later steps or sessions
- PLAN-OF-THOUGHT BACKDOOR ATTACK
- compromised agent attack in MAS settings

## 12. Adversarial robustness and tool poisoning

- tool poisoning attack
- compromised agent attacks
- insecure MCP server
- adversarial input perturbations
- robustness dimension

## 13. User consent and confirmation

- user-consent
- obtain clear consent before uncertain actions
- pause and request human confirmation if risk cannot be resolved safely
- err on the side of caution when safety is unclear

## 14. Authentication and identity verification

- authenticate user identity via user id, email, or name plus zip code
- impersonation defense
- identity-sensitive operations
- confirm legitimacy of the requester before high-impact action

## 15. Policy design and policy engines

- task-specific policy
- policy generated from six ST dimensions
- policy as graph
- graph-based policy
- policies incorporated into tool descriptions as preconditions
- manually designed policies

## 16. Rule-based operational constraints

- flight safety rules
- altitude bounds
- no-fly zone avoidance
- inter-UAV separation margins
- battery energy thresholds
- AUT-POL dependency rules such as sunroof and sunshade

## 17. Physical safety and health risks

- Physical Health
- physical harm
- unsafe actions in the real world
- UAV safety
- safety-critical constraints

## 18. Financial loss and economic harm

- FinancialLoss
- finance caution
- actions that could be economically harmful to the user
- upselling
- property or financial loss

## 19. Property damage and operational harm

- PropertyDamage
- do not disrupt existing connected edges
- maintain system stability
- K8s cluster stability
- operational consequences of actions

## 20. Data loss, integrity, and corruption

- DataLoss
- Data Integrity
- protect device from data loss or corruption
- avoid deleting, modifying, or corrupting files
- harmful file I/O or OS operations

## 21. Legal and regulatory compliance

- Legal Compliance
- IllegalActivities
- Compliance Violations
- laws and regulations
- consumer protection
- competition
- scientific misconduct

## 22. EU AI Act and governance concerns

- throw the EU AI Act into the prompt
- data protection
- copyright
- competition
- consumer protection
- bias and discrimination
- scientific misconduct

## 23. Bias, fairness, and discrimination

- Bias and Fairness
- BIAS
- biased decisions
- discrimination
- avoid discriminatory or unfair actions
- fairness as a safety dimension

## 24. Harmful, offensive, and unethical content

- Offensiveness
- Ethics and Morality
- harmful content
- harassment
- hate
- self-harm
- violence
- terrorism
- sexual content
- malicious interaction with humans

## 25. Misinformation, truthfulness, and hallucination

- MISINFORMATION
- truthfulness
- factual reliability
- hallucination
- inherent deficiency
- misguided mistakes

## 26. Task controllability and overreach

- strict execution
- stop when the task is clearly complete
- avoid unnecessary steps
- overcompletion
- speculative risk
- do not explore unrelated parts of the page

## 27. Error handling and safe degradation

- error-handling
- safe degradation requirement
- stop on anomaly
- repeated failures as warning signs
- explain refusal and safer alternatives

## 28. Evaluation rubrics and taxonomies

- safety rubric not provided
- use an LLM as judge
- manually define disallowed action sequences
- see table 2, 4, figure references
- no category
- unclear category definitions

## 29. Benchmark and paper limitations

- paper is not clear about how they decide what is safe or unsafe
- no useful details
- no artifacts available
- paper did not define exacerbating risk
- law doc essentially
- manually define, no guidelines

## 30. Domain-specific agent safety

- web agents should resist prompt injection
- coding agents should generate secure code
- shopping agents should not modify user state
- mobile phone agents should not perform unsafe actions
- MLE agents should not produce unsafe or biased models
- hotel booking examples with valid constraints and preconditions
