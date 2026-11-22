"""Deterministic, human-centred anomaly triage policy for AIEMS.

This classifies corroborated operational signals. It does not identify students,
infer intent, establish misconduct, or issue disciplinary decisions.
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
    """Apply the diagram's deterministic decision table in safe precedence order."""
    if inputs.approved_exception:
        return Decision(
            rule_id="R1", priority=Priority.SUPPRESSED,
            primary_action="Suppress automated alert; retain an exception audit log.",
            invigilator_guidance="Confirm the approved accommodation/exception record; do not treat it as an anomaly.",
            requires_human_review=False,
        )

    if inputs.signal_anomaly and not inputs.behavioral_cue and not inputs.persistence_or_corroboration:
        return Decision(
            rule_id="R2", priority=Priority.BACKGROUND,
            primary_action="Create a low-priority background log; do not interrupt the examination.",
            invigilator_guidance="No immediate action. Review only if additional independent evidence appears.",
            requires_human_review=False,
        )

    if inputs.persistence_or_corroboration and inputs.signal_anomaly and inputs.behavioral_cue:
        return Decision(
            rule_id="R6", priority=Priority.HUMAN_VERIFICATION,
            primary_action="Raise a high-priority verification cue.",
            invigilator_guidance="Perform a discreet, proportionate physical check and document observable facts. Do not infer intent.",
            requires_human_review=True,
        )

    if inputs.behavioral_cue and inputs.persistence_or_corroboration:
        return Decision(
            rule_id="R5", priority=Priority.HUMAN_VERIFICATION,
            primary_action="Raise a high-priority verification cue.",
            invigilator_guidance="Request discreet human verification; record context and allow the student to respond.",
            requires_human_review=True,
        )

    if inputs.signal_anomaly or inputs.behavioral_cue or inputs.persistence_or_corroboration:
        rule = "R3" if inputs.signal_anomaly and inputs.behavioral_cue else "R4"
        return Decision(
            rule_id=rule, priority=Priority.BACKGROUND,
            primary_action="Record a low-priority background cue for contextual review.",
            invigilator_guidance="Do not interrupt or accuse. Wait for independent corroboration or follow normal supervision.",
            requires_human_review=False,
        )

    return Decision(
        rule_id="R0", priority=Priority.BACKGROUND,
        primary_action="No anomaly action; retain routine system telemetry only.",
        invigilator_guidance="No action required.",
        requires_human_review=False,
    )
