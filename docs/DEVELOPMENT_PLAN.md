# Development Plan and Division of Responsibilities

## Project objective

Build an academic prototype that supports student identity checks before examinations, records attendance, and routes uncertain cases to invigilators for manual review.

## Delivery phases

| Phase | Deliverable | Lead |
|---|---|---|
| 1 | Repository scaffold, Django setup, SQLite configuration | Samuel |
| 2 | Initial template and static asset layout | Frontend developer |
| 3 | Data models and migrations | Samuel |
| 4 | Authentication and role permissions | Samuel |
| 5 | Login and role-specific dashboard interfaces | Both |
| 6 | Student and invigilator management | Both |
| 7 | Examination scheduling and registration | Both |
| 8 | Simulated fingerprint enrollment and verification | Samuel |
| 9 | Fingerprint interaction interface | Frontend developer |
| 10 | Facial enrollment and recognition service evaluation | Samuel |
| 11 | Webcam capture and submission interface | Frontend developer |
| 12 | Combined verification and manual-review workflow | Samuel |
| 13 | Attendance and audit history | Both |
| 14 | Reports and statistics | Both |
| 15 | Integration, security review, testing, and documentation | Both |

## Backend ownership — Samuel

- `config/`: Django settings, root URLs, ASGI and WSGI configuration.
- `integrity/`: models, forms, views, URLs, permissions, admin configuration.
- `integrity/services/`: fingerprint adapter, face recognition adapter, combined verification, attendance rules.
- `integrity/tests/`: automated backend tests.
- Database migrations, authentication, authorization, API contracts, validation, and audit logging.

## Frontend ownership

- `templates/`: Django templates and reusable page layouts.
- `static/css/`: responsive stylesheets.
- `static/js/`: webcam capture, form behavior, API requests, and user feedback.
- `static/images/`: non-sensitive branding and interface assets.

## Shared responsibilities

Agree on model fields, URL names, permissions, CSRF handling, and API request/response schemas before integration. Coordinate edits to `settings.py`, root and app URL configuration, and shared base templates.

## Definition of done

A feature is complete only when its backend rules, user interface, permissions, validation, error handling, tests, and documentation have been reviewed. A visual simulation must be clearly labelled as a simulation and must not be represented as a real biometric match.
