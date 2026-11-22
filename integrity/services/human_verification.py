"""Explicit R6 human-verification workflow policy.

This module governs workflow transitions only. It never determines whether
misconduct occurred; that conclusion remains with authorized human processes.
"""
from dataclasses import dataclass
from enum import StrEnum

class CaseStatus(StrEnum):
    ALERTED = "alerted"
    CHECK_IN_PROGRESS = "check_in_progress"
    BENIGN_CLOSED = "benign_closed"
    REPORT_DRAFT = "report_draft"
    SUBMITTED = "submitted"

class WorkflowError(ValueError):
    """Raised when a requested case transition is not permitted."""

@dataclass(frozen=True)
class Transition:
    status: CaseStatus
    audit_action: str
    requires_notes: bool = False

_ALLOWED = {
    CaseStatus.ALERTED: {"begin_check": Transition(CaseStatus.CHECK_IN_PROGRESS, "r6_check_started")},
    CaseStatus.CHECK_IN_PROGRESS: {
        "benign": Transition(CaseStatus.BENIGN_CLOSED, "r6_benign_closed", True),
        "evidence": Transition(CaseStatus.REPORT_DRAFT, "incident_report_draft_created", True),
    },
    CaseStatus.REPORT_DRAFT: {"submit": Transition(CaseStatus.SUBMITTED, "formal_case_submitted", True)},
}

def transition_case(current_status: str, action: str, notes: str = "") -> Transition:
    """Validate one human workflow transition and return its auditable result."""
    try:
        status = CaseStatus(current_status)
    except ValueError as exc:
        raise WorkflowError("Unknown case status.") from exc
    transition = _ALLOWED.get(status, {}).get(action)
    if transition is None:
        raise WorkflowError("This action is not permitted from the current case status.")
    if transition.requires_notes and not notes.strip():
        raise WorkflowError("A factual note is required for this transition.")
    return transition
