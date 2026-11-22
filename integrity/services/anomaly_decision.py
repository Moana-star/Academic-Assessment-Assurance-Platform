"""Deterministic, human-centred anomaly triage policy for AIEMS.

This classifies operational cues. It does not identify students, infer intent,
establish misconduct, or issue disciplinary decisions.

The supplied decision-table image shows identical C2-C4 symbols for R3 and R4
but different outputs. Until the owner clarifies that source conflict, partial
combinations are deliberately not assigned either rule ID.
"""
from dataclasses import dataclass
from enum import StrEnum


class Priority(StrEnum):
    SUPPRESSED = "suppressed"
    BACKGROUND = "low_priority_background"
    HUMAN_VERIFICATION = "high_priority_human_verification"


@dataclass(frozen=True)
class AnomalyInputs:
    approved_exception: bool = False
    signal_anomaly: bool = False
    behavioral_cue: bool = False
    persistence_or_corroboration: bool = False


@dataclass(frozen=True)
class Decision:
    rule_id: str
    priority: Priority
    primary_action: str
    invigilator_guidance: str
    requires_human_review: bool
    disciplinary_action: bool = False


def evaluate(inputs: AnomalyInputs) -> Decision:
    """Apply unambiguous precedence and conservative handling of partial cues."""
    if inputs.approved_exception:
        return Decision(
            rule_id="R1", priority=Priority.SUPPRESSED,
            primary_action="Suppress alert; log the approved accommodation.",
            invigilator_guidance="No invigilator notification or intervention. Proceed normally.",
            requires_human_review=False,
        )

    if inputs.signal_anomaly and not inputs.behavioral_cue and not inputs.persistence_or_corroboration:
        return Decision(
            rule_id="R2", priority=Priority.BACKGROUND,
            primary_action="Low-priority background log.",
            invigilator_guidance="Transient noise; no immediate action.",
            requires_human_review=False,
        )

    if inputs.signal_anomaly and inputs.behavioral_cue and inputs.persistence_or_corroboration:
        return Decision(
            rule_id="R6", priority=Priority.HUMAN_VERIFICATION,
            primary_action="High-priority verification cue; open an incident draft.",
            invigilator_guidance="Alert the senior invigilator for a discreet standardized check. Escalation requires human corroboration.",
            requires_human_review=True,
        )

    if inputs.signal_anomaly or inputs.behavioral_cue or inputs.persistence_or_corroboration:
        return Decision(
            rule_id="PARTIAL_UNRESOLVED", priority=Priority.BACKGROUND,
            primary_action="Retain a low-priority background record pending clarification of R3/R4 source conditions.",
            invigilator_guidance="Do not interrupt or accuse. Follow normal supervision and seek independent corroboration.",
            requires_human_review=False,
        )

    return Decision(
        rule_id="R0", priority=Priority.BACKGROUND,
        primary_action="No anomaly action; retain routine system telemetry only.",
        invigilator_guidance="No action required.",
        requires_human_review=False,
    )
