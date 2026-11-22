# AIEMS Diagram-Aligned System Specification

This specification combines the diagrams supplied in the WhatsApp video and
the separately supplied full-resolution deterministic decision table. It
describes the intended system; optional hardware and institutional integrations
are not claimed as deployed.

## 1. Level 0 system context

The central system is the **AI-Assisted Examination Integrity Management
System (AIEMS)**.

| External actor/system | Information sent to AIEMS | Information returned by AIEMS |
|---|---|---|
| Invigilator (mobile/tablet UI) | Observations, incident reports, verification outcomes | Discreet alert cues, seating/roster context, incident-log templates |
| Student (indirect) | Responses through invigilator and approved accommodation process | Clear disclosure, accessible manual verification, formal response/appeal route |
| Examination Administration / SIS | Examination schedules, student rosters, seating plans, approved accommodation records | Attendance verification, incident summaries, administrative reports |
| Room Sensors & Network Edge | Aggregated BLE/Wi-Fi signal metadata, anomaly indicators, device/network telemetry | Health checks and configuration requests |
| Disciplinary / Academic Board | Authorized review outcomes and governance decisions | Evidence bundles, case records, audit history |

AIEMS is the system of record for its own application workflow. It is not a
replacement for the SIS, physical room sensors, invigilator judgment, or the
institution's disciplinary authority. The current prototype does not claim
live SIS, BLE/Wi-Fi, or sensor integrations.

## 2. Deterministic invigilator-support decision table

The four inputs are C1 approved exception (for example medical), C2 signal
anomaly (BLE/Wi-Fi), C3 behavioral cue (vision/invigilator), and C4
persistence/corroboration. The full source transcription, including each
row's displayed output and the R3/R4 conflict, is in
[DECISION_TABLE.md](DECISION_TABLE.md).

Unambiguous rows:
- **R1:** approved exception takes precedence; suppress alert and log the
  approved accommodation, with no invigilator notification.
- **R2:** C1=N, C2=Y, C3=N, C4=N; low-priority background log for transient
  noise; no immediate action.
- **R6:** C1=N, C2=Y, C3=Y, C4=Y; high-priority verification cue; alert the
  senior invigilator, require a discreet standardized check, and open an
  incident draft. Escalation still requires human corroboration.

R3 and R4 show identical C1-C4 symbols in the supplied image but different
outputs. They cannot be distinguished deterministically from the visible
inputs. R5's pictograms also need an agreed Boolean interpretation. The code
therefore preserves conservative background handling for unresolved partial
combinations rather than inventing missing conditions.

## 3. R6 swimlane workflow

The workflow diagram's responsibilities are represented as four lanes:

### Room Sensors / AI Engine
1. Passive signal monitoring.
2. Posture/behavior cue analysis.
3. Signal/behavior correlation and persistence assessment.

### AIEMS Hub
1. Receive multiple corroborated anomaly indicators (R6 candidate).
2. Check **Approved Accommodation (C1)?**
3. If yes: suppress escalation and silently log the approved exception.
4. If no: evaluate the R6 condition and issue a correlated high-priority cue.

### Invigilator Mobile UI
1. Receive high-priority discreet cue.
2. Perform a discreet physical/contextual check.
3. Decide whether there is observable evidence requiring a report—not whether
   the student is guilty.
4. If no: record a benign/false-positive reason and close the alert.
5. If concern remains: initiate a formal incident report, prepare the report
   draft, record evidence and the student's response, then submit the formal
   case file through the authorized process.

### Disciplinary Board / Audit
1. Receive the submitted formal case file.
2. Conduct authorized human review and record the outcome.
3. Preserve the action history in an append-only audit trail.

No automated alert is proof of misconduct. No model may skip the invigilator,
the student's opportunity to respond, or the authorized board.

## 4. Functional requirements from the diagrams

- Examination schedules, student rosters, seating plans, and approved
  accommodation records must be available to authorized roles.
- Signal inputs must carry source identity, timestamps, and sufficient
  provenance to support review.
- Rule evaluation must be deterministic and server-side; client-submitted
  priority values must never be trusted.
- Invigilator cues should be discreet, glanceable, and acknowledgeable.
- The human workflow must support both benign closure and formal incident
  reporting, including report draft and case-file submission.
- Audit events must identify actor, timestamp, action, source, and reason.
- A manual verification route must remain available during sensor/network
  failure or where accommodations require it.

## 5. Non-functional requirements

| Area | Diagram-aligned requirement |
|---|---|
| Alert latency | Target delivery below 3–5 seconds after a valid event reaches the application; measure under deployment load |
| Reliability | Graceful manual fallback during network, sensor, or service failure |
| Usability | Silent, glanceable, high-contrast invigilator interface; avoid disruptive student-facing alarms |
| Security | Role-based access, TLS, encryption at rest, CSRF protection, validation, and data isolation |
| Auditability | Append-only event history with actor, timestamp, source, action, and reason |
| Privacy | Metadata-first processing; purpose limitation, retention limits, and deletion workflow |
| Accessibility | Pre-registered accommodations and equivalent manual verification path |

These are design targets, not measured service-level guarantees.

## 6. Ethics, privacy, and governance

- **Support, not surveillance:** no continuous biometric/facial panopticon.
- **False-positive awareness:** alerts are cues, never standalone proof.
- **Equity and accommodations:** approved medical/accessibility accommodations
  suppress escalation; test for device and environmental bias.
- **Data minimization:** metadata-first; define purpose, retention, deletion,
  and access before collecting real student data.
- **Transparency and accountability:** disclose what is collected, why, who
  accesses it, how to challenge it, and how to appeal.
- **Human-in-the-loop due process:** trained human review, recorded reasons,
  student response, and authorized institutional referral.

The governance diagram repeats the Equity & Accommodations label; it is treated
as one principle rather than inventing a separate principle.

## 7. Integration boundaries and prototype status

The current repository provides Django authentication, role-based records,
examination management, a prototype biometric flow, manual review, attendance,
and basic audit records. The following remain integration targets, not
completed production features: SIS connector, BLE/Wi-Fi ingestion, room sensor
gateway, posture analytics, mobile push/real-time alert service, disciplinary
board portal, and externally immutable audit storage.

Do not represent these as live integrations. Use synthetic records and
consenting test participants only; never commit real student records or raw
biometrics.
