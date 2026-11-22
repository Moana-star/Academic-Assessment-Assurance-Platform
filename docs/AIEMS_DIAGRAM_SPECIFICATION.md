# AIEMS Diagram-Aligned System Specification

This specification translates the supplied context, decision-table, workflow,
requirements, and ethics diagrams into repository-level design rules. It does
not claim optional hardware integrations are already deployed.

## 1. System context (Level 0)

The AI-Assisted Examination Integrity Management System (AIEMS) is the central
application boundary.

| External actor/system | Information sent to AIEMS | Information returned by AIEMS |
|---|---|---|
| Invigilator (mobile/tablet UI) | Observations, incident reports, verification outcomes | Alert cues, seating maps, incident-log templates |
| Student (indirect) | Responses through the invigilator and approved accommodation process | Clear disclosure, accessible manual verification, formal appeal route |
| Exam Administration / SIS | Exam schedules, student rosters, seating plans, accommodation data | Incident summaries, attendance verification, administrative reports |
| Room sensors / network edge | Aggregated signal metadata (for example BLE/Wi-Fi anomaly indicators) and system telemetry | Health checks and configuration requests |
| Disciplinary / Academic Board | Case review outcomes and governance decisions | Evidence bundles and append-only audit history |

The application is the system of record for its own workflow, not a replacement
for the SIS, room hardware, or the institution's disciplinary authority.
External integrations must be authenticated, least-privilege, validated, and
audited. Raw sensor streams and continuous biometric surveillance are outside
the current prototype scope.

## 2. Deterministic decision table

Policy inputs are Boolean, server-validated indicators:
- approved_exception: an accommodation or exception is already approved.
- signal_anomaly: an aggregated device/network signal is unusual.
- behavioral_cue: an invigilator records an observable cue.
- persistence_or_corroboration: the cue persists or has independent corroboration.

The policy is implemented in integrity/services/anomaly_decision.py.
Approved exceptions have precedence. A signal-only transient is background
logged. Isolated/partial cues remain low priority. Persistent corroborated
combinations request human verification. No rule issues a disciplinary action.

| Rule | Conditions | System action | Invigilator guidance |
|---|---|---|---|
| R1 | Approved exception = Yes | Suppress alert; retain an exception audit log | Confirm the approved record; do not treat the exception as suspicious |
| R2 | No exception; signal anomaly only; no behavior cue; no persistence | Low-priority background log | No immediate action; wait for independent evidence |
| R3/R4 | One or partial cues without the high-priority corroboration threshold | Low-priority background cue | Do not interrupt or accuse; seek context/corroboration |
| R5 | Behavioral cue + persistence/corroboration | High-priority verification cue | Discreet human verification; document observable facts |
| R6 | Signal anomaly + behavioral cue + persistence/corroboration | High-priority verification cue | Discreet physical check and documented human assessment |

The source image uses icon marks for several R3–R5 cells whose exact values are
not legible in the supplied recording. The implementation encodes the visible
rule intent and conservative threshold, rather than inventing precise sensor
thresholds or claiming a pixel-perfect transcription. Confirm the original
full-resolution decision-table image before treating R3/R4 combinations as
institutionally approved policy.

## 3. High-priority R6 workflow

1. Room/sensor edge performs passive signal monitoring.
2. The edge/application evaluates posture/behavior indicators and correlates
   independent anomalies; the application records signal metadata, not intent.
3. The deterministic engine checks approved accommodations and applies R1–R6.
4. For a high-priority cue, AIEMS creates a discreet alert for the invigilator.
5. The invigilator performs a proportionate physical/contextual check.
6. If the cue is a false positive or benign, record the reason and close it
   without a disciplinary case.
7. If the concern remains, the invigilator initiates a formal incident report,
   records evidence and the student's response, and submits a case file.
8. The authorized board reviews the case and records its outcome.
9. The system retains an append-only audit trail of actions and decisions.

No automated alert is proof of misconduct. No automated model may skip the
invigilator, formal reporting, student's right to respond, or authorized board.

## 4. Functional requirements

- Exam-session and roster lifecycle: schedules, seating, approved accommodations.
- Multi-signal ingestion with source identity, timestamps, and clock-sync metadata.
- Deterministic rule evaluation on the server; browser-submitted priority values are never trusted.
- Discreet invigilator workflow with a target of under 10 seconds for alert delivery/action acknowledgement where deployment supports it.
- Append-only audit events for alert, acknowledgement, observation, incident, review, and closure.
- Human review queue, case notes, evidence references, and appeal/outcome recording.
- Manual identity/attendance route when sensor, network, camera, or accommodation requires it.

## 5. Non-functional requirements

| Area | Requirement |
|---|---|
| Latency | Target alert delivery below 3–5 seconds after a valid event reaches the application; measure in deployment |
| Reliability | Graceful fallback to manual mode during network, sensor, or service failure |
| Usability | Silent, glanceable, high-contrast invigilator interface; avoid disruptive student-facing alarms |
| Security | Role-based access, TLS, encryption at rest, CSRF protection, input validation, and data isolation |
| Auditability | Append-only event history with actor, timestamp, source, action, and reason |
| Privacy | Metadata-first processing; no continuous biometric/facial surveillance; retention limits and deletion workflow |
| Accessibility | Pre-registered accommodations and equivalent manual verification path |

Targets are engineering objectives, not measured service-level guarantees until
load, latency, and failure testing are performed.

## 6. Ethics, privacy, and governance

1. Support, not surveillance: no continuous biometric/facial panopticon.
2. Asymmetric harm and false positives: alerts are cues, never standalone proof.
3. Equity and accommodations: recognize approved medical/accessibility
   accommodations; test for device and environmental bias.
4. Data minimization and retention: metadata-first; define purpose, retention,
   deletion, and access before collecting real student data.
5. Transparency and accountability: disclose what is collected, why, who
   accesses it, how to challenge it, and how to appeal.
6. Human-in-the-loop due process: a trained human reviews context, records
   reasons, hears the student, and refers any formal case to the authorized body.

The supplied diagram repeats the Equity & Accommodations label in two boxes;
this specification treats it as one governance principle rather than
inventing a sixth principle.

## 7. Integration boundaries and prototype status

The current repository provides Django authentication, role-based records,
examination management, a prototype biometric flow, manual review, attendance,
and audit records. It does not yet provide a production SIS connector, room
sensor gateway, BLE/Wi-Fi ingestion, posture analytics, immutable external
audit storage, or a deployed sub-five-second alert service. Those integrations
must be implemented and tested before the diagrams can be described as
fully operational.

Never store raw student biometrics or real student records in Git. Use
synthetic data for demonstrations and consented test participants only.
