# R6 Workflow Implementation Status

## Implemented in the repository

- Persisted incident cases linked to the student, examination, creating user,
  and assigned invigilator.
- Server-side deterministic evaluation. The browser cannot submit its own
  priority, rule ID, or decision.
- R1 approved-exception precedence and R2 transient signal-only background
  handling.
- R6 high-priority cue creation for the explicit C1=N, C2=Y, C3=Y, C4=Y
  combination.
- R3/R4 identical source condition rows and R5 pictogram ambiguity are kept
  out of automatic escalation. They remain background-only until the rule
  owner supplies an unambiguous discriminator / Boolean mapping.
- Role-protected incident desk and assigned-invigilator case access.
- Explicit human transitions: alert → discreet check → benign closure OR
  formal report draft → explicit case submission.
- Formal report requires observations and a recorded student response.
- Dedicated board role, submitted-case queue, and recorded board outcome.
- Append-only audit events at the application/model/admin layer; each
  transition is committed atomically with its audit event.
- Integration tests for R6 creation, R2 handling, human transitions,
  invigilator assignment, board access, and audit event protections.

## Boundaries that remain

- Room sensors, BLE/Wi-Fi telemetry ingestion, vision/posture analytics, SIS
  synchronization, mobile push notifications, and real-time alert delivery
  are not integrated. The current incident desk accepts manually entered
  indicators from authorized staff.
- Audit events are protected against normal application/admin edits and
  deletions, but this is not a cryptographically immutable external audit
  ledger. Production deployment needs database-level controls, restricted
  database roles, backups, and independent tamper monitoring.
- Board outcomes record an application workflow decision only. They do not
  replace institutional disciplinary procedures, legal review, appeal rights,
  or formal records management.
- R3/R4 and R5 require policy-owner clarification before those rows can be
  safely automated.
- The incident workflow and migration are present in the audited repository revision. Whether the migration has been applied to the current production database and whether this exact revision is deployed must be verified separately.

## Verification

The GitHub Actions workflow runs:
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test`

A successful CI run is required before release. Confirm that migration 0004 is applied to the persistent production database as part of an approved deployment plan; never assume that a repository migration has automatically run in production.
