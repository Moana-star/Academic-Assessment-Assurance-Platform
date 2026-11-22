# Academic Assessment Assurance Platform

An academic prototype for examination identity verification, attendance management, and invigilator review.

## Project overview

The Academic Assessment Assurance Platform is designed to support secure and accountable examination administration. It brings together role-based access, student and invigilator records, examination registration, biometric enrollment workflows, attendance tracking, audit history, and manual review of uncertain verification outcomes.

The platform follows an important principle: biometric results are decision-support signals, not automatic proof of misconduct. Any mismatch or inconclusive result must remain available for human review.

## Project status

This is a working academic prototype. Authentication, role guards, records, enrollment interfaces, attendance rules, dashboards, and automated tests are included. Hardware fingerprint integration and production-grade facial recognition require further development and independent evaluation.

## Maintainer

**Moana — [@Moana-star](https://github.com/Moana-star)**

This repository is maintained and developed independently under the Moana-star GitHub account.

## Technology stack

- **Backend:** Python and Django
- **Frontend:** Django templates, HTML5, CSS3, and Vanilla JavaScript
- **Database:** SQLite for local development; managed PostgreSQL when `DATABASE_URL` is configured (deployment)
- **Image processing:** OpenCV
- **Version control:** Git and GitHub

## Core capabilities

- Role-based administrator, invigilator, and student access
- Student and invigilator record management
- Examination scheduling and student registration
- Biometric enrollment workflows
- Simulated fingerprint verification in the initial prototype
- Supervised face-capture and prototype verification flow with inconclusive outcomes routed to human review
- Auditable human-review decisions and duplicate-safe attendance recording
- Facial enrollment and image-processing workflow
- Combined verification outcomes and manual review
- Attendance records, audit history, and reports

## Project principles

1. Biometric results are decision-support signals, not proof of examination malpractice.
2. Failed, mismatched, or inconclusive checks must be referred for human review.
3. An accessible manual identity-verification route must remain available.
4. The browser captures and submits evidence; trusted backend services perform verification.
5. Do not commit real student photographs, biometric samples/templates, credentials, local databases, or private records.
6. Use consenting volunteers and synthetic records during development.

## Repository structure

```text
.
├── config/                 # Django project configuration
├── integrity/              # Core application
│   ├── migrations/
│   ├── services/            # Biometric, verification, and attendance services
│   └── tests/
├── templates/               # Django HTML templates
├── static/
│   ├── css/                 # Stylesheets
│   ├── js/                  # Browser-side interactions
│   └── images/              # Static assets
├── media/
│   └── student_photos/      # Local uploads (not committed)
├── docs/                    # Architecture and development documentation
├── .env.example
├── .gitignore
├── manage.py
└── requirements.txt
```

## Local development setup

Run these commands in PowerShell from the repository root:

```powershell
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser. The custom user model supports `admin`, `invigilator`, and `student` roles. Never place passwords or secret values in source control.

Run project checks and tests:

```powershell
python manage.py check
python manage.py test
```

## Biometric prototype limitations

The fingerprint workflow is a backend-controlled simulation; a browser cannot directly read an arbitrary USB fingerprint scanner. The face adapter validates images, detects a face with OpenCV, and compares a normalized face crop. This is an educational adapter, not a certified biometric identification system. It does not provide reliable liveness detection, anti-spoofing, or forensic identity proof.

Use only consenting volunteers and synthetic records. Production deployment requires secure key management, encrypted template storage, retention and deletion controls, consent records, TLS, rate limiting, and an independently evaluated recognition model.

## Verification outcome policy

| Fingerprint | Face | System outcome |
|---|---|---|
| Match | Match | Eligible for verified status, subject to backend rules |
| Match | Mismatch | Manual review |
| Mismatch | Match | Manual review |
| Mismatch | Mismatch | Manual review |
| Unavailable / inconclusive | Any result | Manual review |

The system must not automatically accuse or penalize a student based on a biometric mismatch.

## Security and privacy

Biometric information is highly sensitive. Before implementing enrollment, define informed consent, purpose limitation, retention and deletion, access controls, encryption, and a manual alternative. Prefer protected templates over retaining raw biometric images or fingerprint data. Never use real biometric data in public repository commits.

## Documentation

- [Architecture notes](docs/ARCHITECTURE.md)
- [API contract](docs/API_CONTRACT.md)
- [Development plan](docs/DEVELOPMENT_PLAN.md)
- [Development guide](docs/CONTRIBUTING.md)
- [Demonstration data setup](docs/DEMO_DATA.md)
