# Deterministic Decision Logic Table — Invigilator Support

This document follows the supplied full-resolution decision-table image. The
executable policy is in `integrity/services/anomaly_decision.py`.

## Source transcription

| Rule | C1 Approved exception | C2 Signal anomaly (BLE/Wi-Fi) | C3 Behavioral cue (vision/invigilator) | C4 Persistence/corroboration | Primary action in source | Invigilator guidance in source |
|---|---|---|---|---|---|---|
| R1 | Approved (Y); other cells shown as wildcard/any | Any | Any | Any | **Suppress alert** | Log as approved accommodation. No invigilator notification (protecting equity). |
| R2 | N | Y | N | N | **Low-priority background log** | Transient noise; no immediate action (preventing alert fatigue). |
| R3 | N | Wi-Fi symbol | Person symbol | Handshake/corroboration symbol | **Low-priority background log** | Form incident; no immediate action. |
| R4 | N | Wi-Fi symbol | Person symbol | Handshake/corroboration symbol | **Low-priority background cue** | Alert Senior Invigilator discreetly using a standardized process; corroboration required for escalation. |
| R5 | N | Person symbol | Handshake/corroboration symbol | Handshake/corroboration symbol | **High-priority verification cue** | Alert Senior Invigilator; source wording after this is visually unclear, but indicates a draft/workflow action and corroboration before escalation. |
| R6 | N | Y | Y | Y | **High-priority verification cue** | Alert Senior Invigilator; discreet standardized check required; open incident draft; corroboration required for escalation. |

R1's magnifying-glass symbols are transcribed as wildcard/any because the row
shows the same symbol in all four condition columns while the approved
exception takes precedence.

## Important source consistency issue

R3 and R4 show the same visible C1-C4 values/symbols, yet prescribe different
primary actions and invigilator guidance. As displayed, those rows cannot both
be implemented as a deterministic decision table: identical inputs cannot
select two different outputs. The image does not show an additional condition
that distinguishes them. The implementation therefore does **not** guess
which partial combination is R3 or R4. It keeps unresolved partial cues at
background priority and does not assign either rule ID until the rule owner
clarifies the missing discriminator.

R5 uses pictograms in Boolean-labelled columns rather than explicit Y/N marks.
The source row is preserved above, but the precise Boolean mapping of those
pictograms needs confirmation before claiming exact executable equivalence.

## Implemented safeguards

1. An approved exception suppresses alert escalation and is logged as an
   accommodation; it is not treated as suspicious.
2. The unambiguous transient signal-only R2 case is background-only.
3. The fully explicit R6 condition (C1=N, C2=Y, C3=Y, C4=Y) requests discreet
   human verification and opens an incident draft; it does not establish
   misconduct.
4. R5 is treated as a high-priority human-verification pattern, but its source
   pictograms still need a confirmed Boolean interpretation.
5. Unresolved partial combinations remain background-only and are not
   incorrectly labelled R3 or R4.
6. No rule makes a disciplinary finding or automatically punishes a student.

The table should be considered a faithful transcription of the visible image,
not a claim that the conflicting R3/R4 rows have been fully operationalized.
