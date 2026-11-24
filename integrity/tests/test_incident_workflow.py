from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from integrity.models import (
    Examination, ExaminationRegistration, IncidentAuditEvent, IncidentCase, Invigilator, Student,
)


User = get_user_model()


class IncidentWorkflowIntegrationTests(TestCase):
    def setUp(self):
        self.invigilator_user = User.objects.create_user(
            username='invigilator-one', password='test-pass-12345', role='invigilator'
        )
        self.invigilator = Invigilator.objects.create(
            user=self.invigilator_user, staff_number='INV-001',
            full_name='Test Invigilator', department='Computing',
        )
        self.student_user = User.objects.create_user(
            username='student-one', password='test-pass-12345', role='student'
        )
        self.student = Student.objects.create(
            user=self.student_user, admission_number='STU-001',
            full_name='Test Student', course='Computer Science',
            department='Computing',
        )
        self.exam = Examination.objects.create(
            title='Test Examination', code='TEST-101', course='Computer Science',
            examination_date=date.today(), start_time=time(9), end_time=time(12),
            venue='Room A', status=Examination.Status.ACTIVE,
        )
        self.exam.invigilators.add(self.invigilator)
        ExaminationRegistration.objects.create(
            student=self.student, examination=self.exam
        )

    def test_r6_creates_persisted_case_and_audit_event(self):
        self.client.force_login(self.invigilator_user)
        response = self.client.post(reverse('incident_create'), {
            'student_id': self.student.pk,
            'examination_id': self.exam.pk,
            'signal_anomaly': 'on',
            'behavioral_cue': 'on',
            'persistence_or_corroboration': 'on',
        })
        self.assertEqual(response.status_code, 302)
        case = IncidentCase.objects.get()
        self.assertEqual(case.rule_id, 'R6')
        self.assertEqual(case.status, IncidentCase.Status.ALERTED)
        self.assertEqual(case.events.count(), 1)

    def test_transient_r2_is_logged_without_opening_case(self):
        self.client.force_login(self.invigilator_user)
        response = self.client.post(reverse('incident_create'), {
            'student_id': self.student.pk,
            'examination_id': self.exam.pk,
            'signal_anomaly': 'on',
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(IncidentCase.objects.exists())

    def test_human_check_benign_close_and_audit_are_persisted(self):
        case = self.make_r6_case()
        self.client.force_login(self.invigilator_user)
        self.client.post(reverse('incident_detail', args=[case.pk]), {'action': 'begin_check'})
        case.refresh_from_db()
        self.assertEqual(case.status, IncidentCase.Status.CHECK_IN_PROGRESS)
        self.client.post(reverse('incident_detail', args=[case.pk]), {
            'action': 'benign', 'notes': 'No independent corroboration observed.',
        })
        case.refresh_from_db()
        self.assertEqual(case.status, IncidentCase.Status.BENIGN_CLOSED)
        self.assertEqual(case.events.count(), 3)

    def test_formal_report_requires_student_response_and_explicit_submission(self):
        case = self.make_r6_case()
        self.client.force_login(self.invigilator_user)
        self.client.post(reverse('incident_detail', args=[case.pk]), {'action': 'begin_check'})
        response = self.client.post(reverse('incident_detail', args=[case.pk]), {
            'action': 'evidence', 'notes': 'Observed facts recorded.',
            'student_response': 'Student response recorded.',
            'formal_report': 'Formal report draft content.',
        })
        case.refresh_from_db()
        self.assertEqual(case.status, IncidentCase.Status.REPORT_DRAFT)
        self.client.post(reverse('incident_detail', args=[case.pk]), {
            'action': 'submit', 'notes': 'Reviewed and submitted by invigilator.',
        })
        case.refresh_from_db()
        self.assertEqual(case.status, IncidentCase.Status.SUBMITTED)

    def test_unassigned_invigilator_cannot_open_case_for_exam(self):
        other_user = User.objects.create_user(
            username='other-invigilator', password='test-pass-12345', role='invigilator'
        )
        self.client.force_login(other_user)
        response = self.client.post(reverse('incident_create'), {
            'student_id': self.student.pk,
            'examination_id': self.exam.pk,
            'signal_anomaly': 'on', 'behavioral_cue': 'on',
            'persistence_or_corroboration': 'on',
        })
        self.assertEqual(response.status_code, 404)
        self.assertFalse(IncidentCase.objects.exists())

    def test_audit_events_cannot_be_edited_or_deleted(self):
        case = self.make_r6_case()
        event = case.events.first()
        with self.assertRaises(ValueError):
            event.save()
        with self.assertRaises(ValueError):
            event.delete()

    def test_board_can_review_only_submitted_case_and_record_outcome(self):
        case = self.make_r6_case()
        case.status = IncidentCase.Status.SUBMITTED
        case.formal_report = 'Submitted report.'
        case.student_response = 'Student response.'
        case.save()
        board_user = User.objects.create_user(
            username='board-reviewer', password='test-pass-12345', role='board'
        )
        self.client.force_login(board_user)
        response = self.client.post(reverse('incident_detail', args=[case.pk]), {
            'action': 'board_review',
            'board_outcome': IncidentCase.BoardOutcome.NO_ACTION,
            'notes': 'Evidence did not support further action.',
        })
        self.assertEqual(response.status_code, 302)
        case.refresh_from_db()
        self.assertEqual(case.status, IncidentCase.Status.BOARD_REVIEWED)
        self.assertEqual(case.board_reviewer, board_user)
        self.assertEqual(case.events.count(), 2)
        self.assertEqual(case.events.last().action, 'board_outcome_recorded')

    def test_board_cannot_open_unsubmitted_case(self):
        case = self.make_r6_case()
        board_user = User.objects.create_user(
            username='board-reviewer', password='test-pass-12345', role='board'
        )
        self.client.force_login(board_user)
        response = self.client.get(reverse('incident_detail', args=[case.pk]))
        self.assertEqual(response.status_code, 404)

    def make_r6_case(self):
        case = IncidentCase.objects.create(
            student=self.student, examination=self.exam,
            created_by=self.invigilator_user, assigned_invigilator=self.invigilator_user,
            rule_id='R6', signal_anomaly=True, behavioral_cue=True,
            persistence_or_corroboration=True, priority='high_priority_human_verification',
            primary_action='High-priority verification cue; open an incident draft.',
            guidance='Discreet standardized human check required.',
        )
        IncidentAuditEvent.objects.create(
            case=case, actor=self.invigilator_user,
            action='alert_created', details='R6 alert created for integration test.',
        )
        return case
