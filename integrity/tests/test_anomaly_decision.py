from django.test import SimpleTestCase

from integrity.services.anomaly_decision import AnomalyInputs, Priority, evaluate


class AnomalyDecisionTests(SimpleTestCase):
    def test_approved_exception_takes_precedence(self):
        result = evaluate(AnomalyInputs(True, True, True, True))
        self.assertEqual(result.rule_id, "R1")
        self.assertEqual(result.priority, Priority.SUPPRESSED)
        self.assertFalse(result.requires_human_review)
        self.assertFalse(result.disciplinary_action)

    def test_transient_signal_only_is_background_logged(self):
        result = evaluate(AnomalyInputs(signal_anomaly=True))
        self.assertEqual(result.rule_id, "R2")
        self.assertEqual(result.priority, Priority.BACKGROUND)
        self.assertFalse(result.requires_human_review)

    def test_partial_or_isolated_cues_do_not_trigger_high_priority(self):
        cases = (
            AnomalyInputs(behavioral_cue=True),
            AnomalyInputs(signal_anomaly=True, behavioral_cue=True),
            AnomalyInputs(persistence_or_corroboration=True),
        )
        for inputs in cases:
            with self.subTest(inputs=inputs):
                result = evaluate(inputs)
                self.assertEqual(result.priority, Priority.BACKGROUND)
                self.assertEqual(result.rule_id, "PARTIAL_UNRESOLVED")
                self.assertFalse(result.requires_human_review)

    def test_unresolved_r5_pictogram_combination_stays_background_only(self):
        result = evaluate(AnomalyInputs(behavioral_cue=True, persistence_or_corroboration=True))
        self.assertEqual(result.rule_id, "PARTIAL_UNRESOLVED")
        self.assertEqual(result.priority, Priority.BACKGROUND)
        self.assertFalse(result.requires_human_review)
        self.assertFalse(result.disciplinary_action)

    def test_correlated_signals_request_human_verification(self):
        result = evaluate(AnomalyInputs(signal_anomaly=True, behavioral_cue=True, persistence_or_corroboration=True))
        self.assertEqual(result.rule_id, "R6")
        self.assertTrue(result.requires_human_review)
        self.assertFalse(result.disciplinary_action)

    def test_no_signal_produces_no_anomaly_action(self):
        result = evaluate(AnomalyInputs())
        self.assertEqual(result.rule_id, "R0")
        self.assertFalse(result.requires_human_review)
