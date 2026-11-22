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
- Deterministic AIEMS anomaly triage policy (R1–R6), with approved-exception precedence and human verification for high-priority cues

## Prototype boundaries

The repository does not yet include a production SIS connector, room-sensor gateway, BLE/Wi-Fi ingestion, posture analytics, certified biometric recognition, or an externally immutable audit store. These are documented integration targets, not completed features. Do not represent them as deployed capabilities.

## Safety and privacy

- A sensor or biometric mismatch is not proof of cheating.
- Approved accommodations take precedence over alert escalation.
- Partial or transient cues remain low priority.
- High-priority cues request discreet human verification.
- Students must receive transparency, an opportunity to respond, and an appeal route.
- Use synthetic records and consenting test participants only.
- Never commit credentials, raw biometrics, real student photographs, private records, or local databases.

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
