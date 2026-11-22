# AIEMS Workflow and Governance Controls

## R6 high-priority workflow

Passive signal monitoring → posture/behavior cue analysis → multi-signal
correlation → approved-accommodation check → discreet invigilator alert →
physical/contextual verification → false-positive closure OR formal incident
report → evidence and student response → formal case file → board review →
append-only audit history.

The application must preserve both branches after human verification:
- **Benign / false positive:** document why, close the alert, and retain an
  audit entry. No disciplinary referral.
- **Concern remains:** create a formal incident record with observed facts,
  source/time metadata, evidence references, and the student's response. The
  authorized board—not the alert engine—decides the outcome.

## Governance checklist

- [ ] Approved accommodation checked before alert escalation.
- [ ] Alert contains source, timestamp, rule ID, and a plain-language reason.
- [ ] No sensitive raw sensor feed is shown to unauthorized roles.
- [ ] Invigilator can acknowledge, record context, and close a false positive.
- [ ] Student receives a clear explanation and an opportunity to respond.
- [ ] Formal report is distinct from automated cue and board outcome.
- [ ] Appeal route and responsible institutional contact are disclosed.
- [ ] Audit events include actor, action, timestamp, and reason.
- [ ] Retention and deletion schedule is approved before real data collection.
- [ ] Manual fallback is available for network/device/accessibility failure.

## Non-goals

The alert system must not:
- continuously capture faces or biometrics;
- infer guilt, intent, or cheating from a BLE/Wi-Fi signal;
- autonomously interrupt, punish, suspend, or disqualify a student;
- treat a sensor anomaly as a formal incident without human verification;
- silently bypass approved accommodations or due-process safeguards.
