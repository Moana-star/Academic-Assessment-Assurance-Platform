# Development Plan

## Project objective

Build an academic prototype that supports student identity checks before examinations, records attendance, and routes uncertain cases to invigilators for manual review.

## Delivery phases

| Phase | Deliverable |
|---|---|
| 1 | Repository structure, Django setup, and local database configuration |
| 2 | Application templates and static asset structure |
| 3 | Data models and database migrations |
| 4 | Authentication and role-based permissions |
| 5 | Login and role-specific dashboard interfaces |
| 6 | Student and invigilator management |
| 7 | Examination scheduling and registration |
| 8 | Simulated fingerprint enrollment and verification |
| 9 | Fingerprint interaction interface |
| 10 | Facial enrollment and recognition-service evaluation |
| 11 | Webcam capture and submission interface |
| 12 | Combined verification and manual-review workflow |
| 13 | Attendance records and audit history |
| 14 | Reports and statistics |
| 15 | Integration, security review, testing, and documentation |

## Application structure

- `config/`: Django settings, root URLs, ASGI, and WSGI configuration.
- `integrity/`: models, forms, views, URLs, permissions, admin configuration, and tests.
- `integrity/services/`: fingerprint adapter, face-processing adapter, combined verification, and attendance rules.
- `templates/`: Django templates and reusable page layouts.
- `static/css/`: responsive stylesheets.
- `static/js/`: webcam capture, form behavior, API requests, and user feedback.
- `static/images/`: non-sensitive branding and interface assets.

## Integration requirements

Coordinate model fields, URL names, permissions, CSRF handling, and API request/response schemas whenever application modules are integrated. Changes to shared settings, URL configuration, and base templates should be checked across the application.

## Definition of done

A feature is complete only when its backend rules, user interface, permissions, validation, error handling, tests, and documentation have been reviewed. A visual simulation must be clearly labelled as a simulation and must not be represented as a real biometric match.
