# Academic Assessment Assurance Platform

A Django-based examination administration system for controlled student registration, staff-led identity checks, attendance, incident documentation, human review, board decisions, reporting, and audit history.

## Core workflows

- Role-based access for administrators, invigilators, students, and board reviewers.
- Student, invigilator, examination, and examination-registration records.
- Staff-led identity verification: an authorised invigilator checks an original institutional student card or another approved document against the student's examination registration.
- Attendance is recorded only after a staff member explicitly records a verified identity check. Uncertain or unsuccessful checks are referred for a second human review; they are not automatically treated as absence or misconduct.
- Manual review decisions require written reasons and are recorded in the audit history.
- Incident records support discreet checks, factual observations, student responses, formal report submission, and board outcomes.
- Reports are calculated from saved attendance, identity-check, review, and audit records.

## Identity verification and privacy

- Simulated fingerprint scans, face capture, facial-template processing, and prototype biometric matching have been removed from the active application workflow.
- The application does not claim to perform biometric identity recognition.
- Staff must inspect the original document in person and compare it with authorised institutional records.
- Do not upload or store identity-document photographs or full document numbers in the application. Record only the document type and the minimum factual notes required for accountability.
- A failed or uncertain identity check is not proof of cheating, fraud, or absence.
- Historical biometric database tables are retained for migration compatibility and preservation of existing records; the application no longer creates or uses new biometric profiles or verification results.

## Incident governance

- Rule-based cues are decision-support only and never establish misconduct.
- Approved accommodations take precedence over escalation.
- Partial or transient cues remain unresolved.
- Human review, student response, documented reasons, and board-level outcomes are separate workflow steps.
- Incident audit events are append-only at the application layer; this is not an externally immutable ledger.

## Known integration boundaries

The repository does not include an institutional student-information-system connector, room-sensor gateway, BLE/Wi-Fi ingestion, posture analytics, real-time alert delivery, or an externally immutable audit store. These must not be represented as implemented capabilities.

## Technology

- Python and Django
- Django templates, HTML, CSS, and vanilla JavaScript
- SQLite for local development; PostgreSQL when DATABASE_URL is configured
- Git and GitHub

## Local development

Run from the repository root in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Run checks and tests:

```powershell
python manage.py check
python manage.py makemigrations --check
python manage.py test
```

## Maintainer

Moana — [@Moana-star](https://github.com/Moana-star)
