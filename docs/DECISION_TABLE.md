# Deterministic Decision Table — AIEMS

The executable policy lives in integrity/services/anomaly_decision.py.
It returns a rule ID, priority, primary action, invigilator guidance, and an
explicit requires_human_review flag. It never returns a disciplinary verdict.

| Rule | Approved exception | Signal anomaly | Behavioral cue | Persistent / corroborated | Outcome |
|---|---:|---:|---:|---:|---|
| R1 | Yes | Any | Any | Any | Suppress alert; audit approved exception |
| R2 | No | Yes | No | No | Low-priority background log |
| R3/R4 | No | Partial combination | Partial combination | Below high-priority threshold | Low-priority background cue |
| R5 | No | Any | Yes | Yes | High-priority human verification |
| R6 | No | Yes | Yes | Yes | High-priority human verification |
| R0 | No | No | No | No | Routine telemetry only |

## Precedence and safeguards

1. R1 overrides all anomaly indicators when the exception is valid and approved.
2. R6 is selected for the fully corroborated three-signal combination.
3. R5 is selected for persistent/corroborated behavioral cues.
4. All remaining partial signals are background-only.
5. No rule creates attendance, an incident finding, or a disciplinary outcome.
6. A high-priority result means "ask a trained human to verify", not "student
   is cheating".

## Important source limitation

The supplied phone recording does not expose every R3/R4 icon value at
readable resolution. The conservative implementation deliberately groups
unconfirmed partial combinations into background review. The original
full-resolution decision-table image should be checked with stakeholders
before R3/R4 are treated as final institutional policy.
