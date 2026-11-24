# Product and Technical Audit

**Audit date:** 24 November 2026  
**Repository:** `Moana-star/Academic-Assessment-Assurance-Platform`  
**Audited ref:** `main` at `f21b93a76ac33c6f7bb99e35496f0e609261005c`  
**Product direction:** Premium university enterprise experience; complete transformation; prototype now with a documented path to validated hardware.

## Executive assessment

The repository is a working Django academic prototype with a meaningful foundation. It is not yet a complete university examination operations platform and must not be represented as production-grade biometric verification. The existing role model, examination/student records, human review, incident workflow, audit events, encrypted face-template storage, and CI workflow are worth preserving.

The safest transformation is incremental: stabilize the existing behavior, correct authorization and decision boundaries, then introduce the missing academic and examination workflows before a coordinated interface redesign.

## What exists today

- Django project with a custom `integrity.User` model and four roles: administrator, invigilator, student, and board reviewer.
- Student and invigilator profiles; examinations with dates, times, venues, status, and assigned invigilators.
- Examination registration model with a uniqueness constraint.
- Biometric profile, fingerprint placeholder service, educational OpenCV face-processing service, and verification logs.
- Attendance records with a uniqueness constraint and a manual-review queue.
- Incident case workflow with server-side rule evaluation, assigned invigilators, student response, formal report draft, board outcome, and append-only application-level incident audit events.
- Audit log, synthetic demo-data command, Django templates, CSS, vanilla JavaScript, and GitHub Actions checks.
- SQLite local-development fallback and PostgreSQL configuration when `DATABASE_URL` is supplied.

## CI baseline observed

Latest GitHub Actions run for the audited main commit: **run 74**.

- `python manage.py check`: passed.
- `python manage.py makemigrations --check --dry-run`: passed; no model/migration drift detected.
- `python manage.py test`: failed with **2 errors out of 39 tests**.

Both failing tests are stale against the current enrollment contract:
- `test_student_can_enroll_fingerprint_without_face_capture`
- `test_admin_can_enroll_selected_student_fingerprint`

They expect a fingerprint-only profile to be saved. The current enrollment view intentionally requires student consent, separate face-processing consent, and a captured face image before saving the combined prototype enrollment. The right repair is to update/add tests to reflect the current consent and capture policy, not weaken the policy just to make CI green.

## Findings and priorities

### P0 — Correct before extending workflows

1. **Keep prototype verification non-authoritative.** The verification service currently forces the combined result to `manual_review`, which is the correct prototype boundary. The view still contains an old `verified` branch that would create PRESENT attendance if a future service returned that value. Remove this unreachable unsafe path and make biometric prototype outcomes incapable of confirming attendance. Only an authorized human decision should create or promote attendance.
2. **Enforce least-privilege data scope.** Dashboard context currently calculates institution-wide counts and recent verification logs for every role. The student dashboard receives global aggregate values. Invigilator attendance, reports, student selectors, and verification lists also need to be scoped to assigned examinations and permitted records. Apply authorization in querysets and views, not only in templates.
3. **Harden production secrets.** `SECRET_KEY` currently has a predictable fallback value. Production startup should fail safely when required secrets are absent; configure a strong secret and dedicated biometric encryption key through deployment environment variables.
4. **Validate state-changing requests.** Ensure all approval, review, enrollment, attendance, and incident transitions use POST-only handlers, CSRF protection, transactional updates, and audit entries.
5. **Verify production database behavior.** SQLite is appropriate locally; a persistent managed PostgreSQL database is required for reliable hosted data. Confirm production `DATABASE_URL`, migration execution, backup, and restore before claiming data durability.

### P1 — Complete the product workflows

1. Examination sessions: scheduled/open/paused/closed lifecycle, with authorized session operators and timestamps.
2. Academic structure: academic years, semesters, departments, courses, rooms, capacities, and examination allocations.
3. Registration workflow: assign eligible students to examinations and enforce registration before check-in.
4. Invigilator assignment and workspace filtering by assigned sessions.
5. Student examination pass with examination, venue, time, and registration state.
6. QR check-in using short-lived, session-bound, server-validated tokens; QR is a check-in aid, not identity proof.
7. Manual identity confirmation and an accessible alternative path.
8. Student appeals and response tracking, linked to the underlying attendance or incident record.
9. Report generation and CSV/PDF export with filters, timestamps, and audit trail.
10. Notifications and pending-action inbox.

### P1 — Biometric and privacy boundary

- Fingerprint enrollment is a placeholder; no physical sensor or fingerprint template is read.
- The current face service uses a basic Haar face detector and a 32×32 grayscale image vector. This is not validated identity recognition, liveness detection, or a production biometric algorithm.
- Multi-angle enrollment is not implemented. It would require a separately designed capture workflow and compatible, validated processing method.
- The model has a `facial_capture` field, but the current view stores the encrypted template and discards the original image. Confirm whether this unused field should be removed in a later migration.
- Keep biometric enrollment optional for the academic prototype, use synthetic records/consenting test participants, document separate consent, retention/deletion, access restrictions, key management, and an equivalent manual alternative. Do not purchase or integrate hardware until the scanner make/model, SDK, supported operating environment, and institutional privacy approval are known.

### P2 — Interface and usability

- The current base layout uses a plum/rose palette, not the agreed navy/white/blue enterprise system.
- Navigation is a compact role-conditional list. It needs a consistent desktop sidebar, accessible mobile drawer, active-route state, section grouping, page titles, breadcrumbs, and clear account controls.
- Administrator, invigilator, and student dashboards exist, but the student dashboard is minimal and the invigilator/admin metrics are not consistently scoped.
- The reports page currently displays summaries and recent records; it is not yet a filtered report builder or export workflow.
- Standardize reusable page headers, cards, tables, forms, empty states, status labels, confirmations, validation messages, and responsive behavior. Keep the existing Django-template and vanilla-JavaScript stack.

### P2 — Engineering quality

- Add regression tests for role-based object visibility, POST-only mutations, session lifecycle, exam registration, check-in token expiry/replay, appeal transitions, exports, and data retention.
- Keep migrations versioned and deploy them deliberately; never rely on production auto-creation of tables.
- Add structured logging, useful error pages, database backup/restore drills, upload validation, rate limits for authentication and sensitive endpoints, and production security headers.
- Treat the general `AuditLog` as an operational audit trail, not immutable evidence. Strengthen it with restricted database permissions, controlled retention, and external monitoring before institutional production use.
- The GitHub Actions workflow currently runs Django system checks, migration drift checks, and the test suite. The test suite must be green before each phase is considered complete.

## Recommended transformation sequence

1. **Foundation and safety:** fix CI tests to match the enrollment contract; remove the unsafe automatic biometric attendance branch; scope data by role and assignment; harden secrets and POST-only mutations.
2. **Academic core:** introduce academic years/terms, departments/courses, rooms, examination registrations, and validated examination scheduling.
3. **Examination operations:** implement session lifecycle, invigilator assignment, student examination passes, QR check-in, and manual attendance confirmation.
4. **Integrity and due process:** improve review queues, incident evidence, student responses, appeals, and board workflow; retain human authority over outcomes.
5. **Reporting and governance:** filtered reports, CSV/PDF exports, audit views, consent and retention controls, and backup/restore procedures.
6. **Enterprise UX and release QA:** apply the consistent navy/white/blue design system across all roles; test desktop/mobile/accessibility; verify production migrations, database persistence, security, and end-to-end journeys.

## Acceptance standard

A phase is complete only when:
- every role sees only the records and actions it is authorized to access;
- each important action has server-side validation and an audit event;
- all relevant automated tests pass;
- migrations are clean and deployable;
- the interface works on desktop and mobile;
- no prototype biometric result is presented as verified identity or evidence of misconduct;
- the documented feature status matches what is actually deployed.

## Explicitly not claimed as complete

Real fingerprint hardware capture, validated face recognition, liveness detection, QR check-in, live examination-session management, student appeals, production-grade immutable audit storage, and institutional SIS integration are not currently implemented.
