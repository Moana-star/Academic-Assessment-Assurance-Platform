# R6 workflow implementation boundary

The deterministic decision service and this transition policy are separate by design.

## Human-verification states

| Current state | Authorized action | Next state | Required record |
|---|---|---|---|
| Alerted | Begin discreet check | Check in progress | Workflow audit event |
| Check in progress | Record benign outcome | Benign closed | Factual notes |
| Check in progress | Record evidence requiring escalation | Report draft | Factual notes |
| Report draft | Submit formal case | Submitted | Review/submission notes |

## Safety and governance invariants

- An automated anomaly cue is not a finding of misconduct.
- A high-priority cue requests a human check; it does not automatically create a disciplinary finding.
- A benign outcome closes the workflow without creating a formal case.
- A formal report is a draft until an authorized person submits it.
- The transition policy rejects skipped steps and requires notes for consequential outcomes.
- Production persistence, role authorization, notification delivery, board review, and append-only audit storage must be wired into Django views/models before this workflow can be called end-to-end complete.

## Validation

Run python manage.py test integrity.tests to execute the workflow and decision tests.

This document intentionally distinguishes tested policy logic from full production integration.
