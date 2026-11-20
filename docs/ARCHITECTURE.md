# Architecture Notes

## High-level flow

1. An authorized administrator registers a student and examination.
2. Enrollment is performed with informed consent and a documented retention policy.
3. The browser requests camera access and submits a captured image over an authenticated, protected request.
4. Django validates the request and delegates processing to backend service modules.
5. Fingerprint and face services return explicit outcomes such as match, mismatch, unavailable, or inconclusive.
6. The combined verification service applies server-side policy.
7. Confirmed attendance is recorded once; uncertain outcomes create a manual-review task.
8. Authorized invigilators record the outcome of the manual check, with an audit entry.

## Separation of concerns

- Templates render interface structure.
- JavaScript captures user input and communicates with Django.
- Views validate requests and enforce permissions.
- Service modules encapsulate biometric and attendance rules.
- Models persist records and relationships.
- Tests verify behavior and security boundaries.

## Biometric design cautions

Face detection is not identity recognition. Select and evaluate a recognition model before claiming face matching is implemented. Simulated fingerprint checks must be clearly identified as simulation. Do not store raw biometric material unnecessarily; protect templates, restrict access, define deletion/retention, and provide an accessible manual route.
