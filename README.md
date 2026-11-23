# Academic Assessment Assurance Platform

An academic prototype for examination identity verification, attendance management, and invigilator review.

## Project overview

The Academic Assessment Assurance Platform supports accountable examination administration through role-based access, student and invigilator records, examination registration, supervised verification workflows, attendance tracking, audit history, and human review of uncertain outcomes.

Biometric and operational signals are decision-support cues, not proof of misconduct. Automated rules must never issue disciplinary decisions.

## Diagram-aligned documentation

- [Architecture notes](docs/ARCHITECTURE.md)
- [AIEMS context, requirements, and diagram specification](docs/AIEMS_DIAGRAM_SPECIFICATION.md)
- [Deterministic decision table](docs/DECISION_TABLE.md)
- [R6 workflow and governance controls](docs/WORKFLOW_AND_GOVERNANCE.md)
- [API contract](docs/API_CONTRACT.md)
- [Development plan](docs/DEVELOPMENT_PLAN.md)
- [Development guide](docs/CONTRIBUTING.md)
- [Demonstration data setup](docs/DEMO_DATA.md)

## Technology

- Python and Django
- Django templates, HTML, CSS, and vanilla JavaScript
- SQLite for local development; PostgreSQL when DATABASE_URL is configured
- OpenCV educational face-processing adapter
- Git and GitHub

## Core capabilities

- Administrator, invigilator, and student roles
- Student, examination, and registration records
- Prototype biometric enrollment and supervised verification
- Attendance recording and duplicate-safe constraints
- Manual review queue and audit history
- Persisted incident cases, discreet invigilator verification, benign closure, formal report drafting/submission, and a dedicated board outcome workflow
- Deterministic AIEMS triage for unambiguous R1, R2, and R6 patterns; unresolved R3/R4/R5 inputs are deliberately not escalated automatically

## Prototype boundaries

The repository does not yet include a production SIS connector, room-sensor gateway, BLE/Wi-Fi ingestion, posture analytics, real-time alert delivery, certified biometric recognition, or an externally immutable audit store. Incident indicators are currently entered by authorized staff; the new audit history is append-only at the application layer, not a tamper-proof external ledger. These are documented integration targets, not completed features. Do not represent them as deployed capabilities.

## Safety and privacy

- A sensor or biometric mismatch is not proof of cheating.
- Approved accommodations take precedence over alert escalation.
- Partial or transient cues remain low priority.
- High-priority cues request discreet human verification.
- Students must receive transparency, an opportunity to respond, and an appeal route.
- Use synthetic records and consenting test participants only.
- Never commit credentials, raw biometrics, real student photographs, private records, or local databases.

## Biometric security and integration status

- Facial templates are encrypted before database storage using Fernet. Set a dedicated `BIOMETRIC_ENCRYPTION_KEY` in the deployment environment; generate it with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` and keep it stable and private. A key derived from `DJANGO_SECRET_KEY` is used only as a fallback.
- Existing legacy face templates remain readable for compatibility and are replaced with encrypted templates on the next successful face enrollment. Back up the database and preserve the encryption key before rotating secrets.
- The browser camera image is processed in memory; the original capture is not stored. The encrypted template is the only face-derived value retained.
- Student consent is required for enrollment, with separate consent for face processing. Enrollment and verification actions are written to the audit log.
- Fingerprint capture remains a placeholder until a physical scanner, vendor SDK, and trusted server-side adapter are selected. The prototype fingerprint check returns `unavailable`; the lightweight OpenCV face comparison cannot approve attendance. Prototype verification always goes to human review.
- Biometric profiles are excluded from the general Django admin listing. Production use still requires a privacy impact assessment, institutional policy approval, retention/deletion rules, independent security review, and validated hardware/biometric algorithms.

## Local development

Run from the repository root in PowerShell:

```powershell
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Run checks and tests:

```powershell
python manage.py check
python manage.py test
```

## Maintainer

Moana — [@Moana-star](https://github.com/Moana-star)
