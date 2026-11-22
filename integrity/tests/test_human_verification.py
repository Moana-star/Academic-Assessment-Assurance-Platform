from django.test import SimpleTestCase
from integrity.services.human_verification import CaseStatus, WorkflowError, transition_case

class HumanVerificationWorkflowTests(SimpleTestCase):
    def test_r6_alert_can_start_discreet_check(self):
        result = transition_case(CaseStatus.ALERTED, "begin_check")
        self.assertEqual(result.status, CaseStatus.CHECK_IN_PROGRESS)
        self.assertEqual(result.audit_action, "r6_check_started")

    def test_benign_outcome_closes_without_formal_case(self):
        result = transition_case(CaseStatus.CHECK_IN_PROGRESS, "benign", notes="No corroborating evidence observed.")
        self.assertEqual(result.status, CaseStatus.BENIGN_CLOSED)

    def test_evidence_creates_report_draft_not_guilt_finding(self):
        result = transition_case(CaseStatus.CHECK_IN_PROGRESS, "evidence", notes="Observed facts recorded.")
        self.assertEqual(result.status, CaseStatus.REPORT_DRAFT)

    def test_report_draft_must_be_explicitly_submitted(self):
        result = transition_case(CaseStatus.REPORT_DRAFT, "submit", notes="Reviewed by authorized invigilator.")
        self.assertEqual(result.status, CaseStatus.SUBMITTED)

    def test_notes_required_for_outcomes_and_submission(self):
        for status, action in ((CaseStatus.CHECK_IN_PROGRESS, "benign"), (CaseStatus.CHECK_IN_PROGRESS, "evidence"), (CaseStatus.REPORT_DRAFT, "submit")):
            with self.subTest(status=status, action=action):
                with self.assertRaises(WorkflowError):
                    transition_case(status, action)

    def test_cannot_skip_human_check_or_reopen_closed_case(self):
        with self.assertRaises(WorkflowError):
            transition_case(CaseStatus.ALERTED, "evidence", notes="x")
        with self.assertRaises(WorkflowError):
            transition_case(CaseStatus.BENIGN_CLOSED, "submit", notes="x")
