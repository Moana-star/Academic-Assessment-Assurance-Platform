# Academic Assessment Assurance Platform



> **Project provenance and collaboration**
>
> This repository is a separately maintained copy of the collaborative academic examination-integrity project originally developed in [AI-Assisted-Exam-Integrity-System](https://github.com/Moana-star/AI-Assisted-Exam-Integrity-System). It preserves the shared project's code and documented team responsibilities; the new repository name does not imply sole authorship.
>
> **Acknowledgements:** Samuel Kyalo ([@Somba-kyalo](https://github.com/Somba-kyalo)) — backend architecture, Django configuration, models, authentication, permissions, server-side workflows, biometric services, attendance, audit and backend tests. Moana ([@Moana-star](https://github.com/Moana-star)) — frontend development, templates, responsive interface, browser interactions, webcam capture, API integration, validation and accessibility. Shared design and integration decisions remain collaborative.

An academic learning prototype for examination identity verification, attendance management, and invigilator review.

> **Project status:** Working academic prototype. Core authentication, role guards, records, enrollment UI, attendance rules, dashboards, and tests are implemented. Hardware fingerprint integration and production-grade facial recognition remain future adapters.

## Technology stack

- **Backend:** Python and Django
- **Frontend:** Django templates, HTML5, CSS3, and Vanilla JavaScript
- **Database:** SQLite for local academic development
- **Image processing:** OpenCV (planned)
- **Biometrics:** Simulated fingerprint workflow initially; compatible fingerprint hardware integration is a later phase
- **Version control:** Git and GitHub

No React, Node.js, Bootstrap, or frontend framework is part of the planned core stack.

## Project principles

1. Biometric results are decision-support signals, not proof of examination malpractice.
2. A failed or inconclusive check must be referred for human review.
3. An accessible manual identity-verification route must remain available.
4. The browser captures and submits evidence; trusted backend services perform verification.
5. Do not commit real student photographs, biometric samples/templates, credentials, local databases, or private records.
6. Use consenting volunteers and synthetic records during development.

## Planned capabilities

- Role-based administrator, invigilator, and student access
- Student and invigilator records
- Examination scheduling and student registration
- Biometric enrollment workflows
- Simulated fingerprint verification in the first prototype
- Facial enrollment and comparison using an appropriate recognition model
- Combined verification outcomes and manual review
- Attendance, audit history, and reports

## Repository layout

```text
.
├── config/                 # Django project configuration
├── integrity/              # Core domain app
│   ├── migrations/
│   ├── services/            # Biometric, verification, attendance services
│   └── tests/
├── templates/               # Django HTML templates by feature
├── static/
│   ├── css/                 # Feature-specific stylesheets
│   ├── js/                  # Vanilla JavaScript modules
│   └── images/              # Non-sensitive static assets
├── media/
│   └── student_photos/      # Local uploads; ignored by Git
├── docs/                    # Architecture, API contract, collaboration notes
├── .env.example
├── .gitignore
├── manage.py                # Added when Django project setup begins
└── requirements.txt
```

## Team responsibilities

### Samuel — backend

- Django configuration, data models, authentication, permissions, and server-side views/API
- Biometric service interfaces and verification logic
- Attendance, audit logging, validation, and backend tests
- Security and integration support

### Frontend developer — interface

- Django templates and page layouts
- Responsive HTML and CSS
- Vanilla JavaScript interactions and webcam capture
- API integration, validation feedback, loading states, and accessibility

### Shared work

Agree on model fields, URL names, request/response formats, permissions, and integration milestones before connecting modules. Coordinate changes to shared configuration and base templates.

## Development setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. The custom user model supports `admin`, `invigilator`, and `student` roles. Never place a password in source control.

Run validation with:

```powershell
python manage.py check
python manage.py test
```

## Prototype biometric limitations

The fingerprint workflow is deliberately a backend-controlled simulation and is labelled as such in the interface; a browser cannot read an arbitrary USB scanner. The face adapter validates images, detects one face with OpenCV, and compares a normalized face crop. This is an educational adapter, not a certified biometric identification system: it does not provide reliable liveness detection, anti-spoofing, or forensic identity proof. Mismatches and inconclusive results always remain manual-review cases.

The application should be used only with consenting volunteers and synthetic records. Keep `.env`, local databases, uploads, and biometric templates out of public repositories. Production deployment requires key management, encrypted template storage, retention/deletion controls, consent records, TLS, rate limiting, and an independently evaluated recognition model.

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

Biometric information is highly sensitive. Before implementing enrollment, define informed consent, purpose limitation, retention/deletion, access controls, encryption, and a manual alternative. Prefer protected templates over retaining raw biometric images or fingerprint data. Never use real biometric data in public repository commits.

## Collaboration workflow

- Use feature branches for individual tasks.
- Keep commits small and descriptive.
- Open pull requests for review before merging.
- Do not commit `.env`, `db.sqlite3`, uploaded media, virtual environments, or generated secrets.
- Document API contracts before frontend/backend integration.

See [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md), [docs/API_CONTRACT.md](docs/API_CONTRACT.md), and [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).
