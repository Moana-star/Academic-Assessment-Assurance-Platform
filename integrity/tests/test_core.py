from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase

from integrity.models import (
    Attendance, AuditLog, Examination, ExaminationRegistration,
    IdentityVerification, Invigilator, ManualReview, Student,
)
from integrity.services.attendance_service import record


class IntegrityCoreTests(TestCase):
    def setUp(self):
        User = get_user_model()
        student_user = User.objects.create_user(username='student', password='test-pass-123', role='student')
        self.student = Student.objects.create(user=student_user, admission_number='A001', full_name='Test Student', course='BSc', department='Computing')
        self.exam = Examination.objects.create(title='Systems', code='SYS101', course='BSc', examination_date=date.today(), start_time=time(9), end_time=time(11), venue='Hall A', status='active')
        ExaminationRegistration.objects.create(student=self.student, examination=self.exam)

    def make_admin(self, username='admin'):
        return get_user_model().objects.create_user(username=username, password='admin-pass-123', role='admin', is_staff=True)

    def test_duplicate_attendance_is_not_created(self):
        first, created = record(self.student, self.exam, method='staff_identity_check')
        second, created_again = record(self.student, self.exam, method='staff_identity_check')
        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Attendance.objects.count(), 1)

    def test_empty_student_and_examination_lists_render_their_empty_state(self):
        Student.objects.all().delete()
        Examination.objects.all().delete()
        self.client.force_login(self.make_admin('empty-state-admin'))
        students_response = self.client.get('/students/')
        examinations_response = self.client.get('/examinations/')
        self.assertContains(students_response, 'No students registered.')
        self.assertContains(examinations_response, 'No examinations created.')
        self.assertNotContains(students_response, '{empty}')
        self.assertNotContains(examinations_response, '{empty}')

    def test_student_cannot_open_admin_page(self):
        self.client.login(username='student', password='test-pass-123')
        self.assertEqual(self.client.get('/students/').status_code, 403)

    def test_registration_waits_for_admin_approval(self):
        response = self.client.post('/register/', {
            'username': 'pending', 'email': 'pending@example.com',
            'password': 'strong-pass-123', 'password_confirm': 'strong-pass-123',
            'admission_number': 'A002', 'full_name': 'Pending Student', 'course': 'BSc', 'department': 'Computing',
        })
        self.assertEqual(response.status_code, 200)
        pending = get_user_model().objects.get(username='pending')
        self.assertFalse(pending.is_active)
        self.assertFalse(self.client.login(username='pending', password='strong-pass-123'))

    def test_admin_can_approve_account(self):
        pending = get_user_model().objects.create_user(username='pending', password='strong-pass-123', role='student', is_active=False)
        Student.objects.create(user=pending, admission_number='A002', full_name='Pending Student', course='BSc', department='Computing')
        self.client.force_login(self.make_admin())
        response = self.client.post(f'/accounts/{pending.pk}/approve/')
        self.assertRedirects(response, '/accounts/pending/')
        pending.refresh_from_db()
        self.assertTrue(pending.is_active)

    def test_board_user_is_sent_to_dedicated_case_queue(self):
        board = get_user_model().objects.create_user(
            username='board-user', password='board-pass-123',
            role='board',
        )
        self.client.force_login(board)
        response = self.client.get('/')
        self.assertRedirects(response, '/board/cases/')

    def test_dashboard_requires_authentication(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/login/?next=/')

    def test_admin_dashboard_counts_saved_records(self):
        self.client.force_login(self.make_admin('admin-dashboard'))
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['students_count'], 1)
        self.assertEqual(response.context['exams_count'], 1)

    def test_staff_document_check_records_verified_attendance_and_audit(self):
        admin = self.make_admin('verification-admin')
        self.client.force_login(admin)
        response = self.client.post('/verification/', {
            'examination': self.exam.pk, 'admission_number': self.student.admission_number,
            'document_type': 'student_card', 'outcome': 'verified',
            'notes': 'Original student card checked against the approved institutional registration record.',
        })
        self.assertRedirects(response, '/verification/')
        check = IdentityVerification.objects.get()
        self.assertEqual(check.checked_by, admin)
        self.assertEqual(check.outcome, IdentityVerification.Outcome.VERIFIED)
        attendance = Attendance.objects.get(student=self.student, examination=self.exam)
        self.assertEqual(attendance.attendance_status, Attendance.Status.PRESENT)
        self.assertEqual(attendance.verification_method, 'staff_identity_check')
        self.assertTrue(AuditLog.objects.filter(action='identity_manually_verified').exists())

    def test_uncertain_identity_check_is_referred_and_not_marked_present(self):
        self.client.force_login(self.make_admin('review-referral-admin'))
        response = self.client.post('/verification/', {
            'examination': self.exam.pk, 'admission_number': self.student.admission_number,
            'document_type': 'institutional_record', 'outcome': 'referred',
            'notes': 'Name could be confirmed but the presented document photograph was unclear. Requesting second authorised review.',
        })
        self.assertRedirects(response, '/verification/')
        self.assertEqual(IdentityVerification.objects.get().outcome, IdentityVerification.Outcome.REFERRED)
        self.assertEqual(ManualReview.objects.filter(decision='pending').count(), 1)
        attendance = Attendance.objects.get(student=self.student, examination=self.exam)
        self.assertEqual(attendance.attendance_status, Attendance.Status.MANUAL)
        self.assertFalse(Attendance.objects.filter(attendance_status=Attendance.Status.PRESENT).exists())

    def test_identity_could_not_be_verified_does_not_create_absence_or_misconduct_finding(self):
        self.client.force_login(self.make_admin('not-verified-admin'))
        self.client.post('/verification/', {
            'examination': self.exam.pk, 'admission_number': self.student.admission_number,
            'document_type': 'student_card', 'outcome': 'not_verified',
            'notes': 'Candidate could not provide an approved identity document at the time of check.',
        })
        self.assertEqual(IdentityVerification.objects.get().outcome, IdentityVerification.Outcome.NOT_VERIFIED)
        self.assertEqual(Attendance.objects.get().attendance_status, Attendance.Status.MANUAL)
        self.assertEqual(ManualReview.objects.filter(decision='pending').count(), 1)

    def test_identity_check_requires_notes_and_a_valid_document_type(self):
        self.client.force_login(self.make_admin('validation-admin'))
        response = self.client.post('/verification/', {
            'examination': self.exam.pk, 'admission_number': self.student.admission_number,
            'document_type': 'made_up', 'outcome': 'verified', 'notes': '',
        })
        self.assertRedirects(response, '/verification/')
        self.assertFalse(IdentityVerification.objects.exists())
        self.assertFalse(Attendance.objects.exists())

    def test_unregistered_student_cannot_be_checked_for_exam(self):
        other_user = get_user_model().objects.create_user(username='other', password='test-pass-123', role='student')
        Student.objects.create(user=other_user, admission_number='A099', full_name='Unregistered', course='BSc', department='Computing')
        self.client.force_login(self.make_admin('registration-guard-admin'))
        response = self.client.post('/verification/', {
            'examination': self.exam.pk, 'admission_number': 'A099',
            'document_type': 'student_card', 'outcome': 'verified', 'notes': 'Attempted verification.',
        })
        self.assertEqual(response.status_code, 404)
        self.assertFalse(IdentityVerification.objects.exists())

    def test_invigilator_can_only_check_assigned_examinations(self):
        User = get_user_model()
        staff_user = User.objects.create_user(username='invigilator', password='staff-pass-123', role='invigilator')
        invigilator = Invigilator.objects.create(user=staff_user, staff_number='STAFF-1', full_name='Test Invigilator', department='Computing')
        self.client.force_login(staff_user)
        payload = {
            'examination': self.exam.pk, 'admission_number': self.student.admission_number,
            'document_type': 'student_card', 'outcome': 'verified',
            'notes': 'Assigned invigilator checked the original student card against the register.',
        }
        self.assertEqual(self.client.post('/verification/', payload).status_code, 404)
        self.exam.invigilators.add(invigilator)
        response = self.client.post('/verification/', payload)
        self.assertRedirects(response, '/verification/')
        self.assertEqual(IdentityVerification.objects.count(), 1)

    def test_old_biometric_and_demo_routes_are_removed(self):
        self.client.force_login(self.make_admin('legacy-route-admin'))
        self.assertEqual(self.client.get('/biometrics/enroll/').status_code, 404)
        self.assertEqual(self.client.get('/biometrics/verify/').status_code, 404)
        self.assertEqual(self.client.post('/demo-data/load/').status_code, 404)

    def test_human_review_clearance_is_audited_and_records_manual_attendance(self):
        admin = self.make_admin('review-admin')
        review = ManualReview.objects.create(student=self.student, examination=self.exam, reason='Staff identity check was inconclusive.')
        Attendance.objects.create(student=self.student, examination=self.exam, attendance_status=Attendance.Status.MANUAL, verification_method='staff_identity_check_pending')
        self.client.force_login(admin)
        response = self.client.post('/reviews/', {
            'review_id': review.pk, 'decision': 'cleared',
            'notes': 'Second authorised reviewer checked the original institutional record and cleared the candidate.',
        })
        self.assertRedirects(response, '/reviews/')
        review.refresh_from_db()
        self.assertEqual(review.decision, 'cleared')
        attendance = Attendance.objects.get(student=self.student, examination=self.exam)
        self.assertEqual(attendance.verification_method, 'manual_review_approved')
        self.assertTrue(AuditLog.objects.filter(action='manual_review_completed').exists())
