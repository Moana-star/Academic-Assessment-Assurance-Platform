from datetime import date, time
from django.contrib.auth import get_user_model
from django.test import TestCase
from integrity.models import Attendance, AuditLog, BiometricProfile, Examination, ManualReview, Student, VerificationLog
from integrity.services.verification_service import combine
from integrity.services.attendance_service import record

class IntegrityCoreTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username='student', password='test-pass-123', role='student')
        self.student = Student.objects.create(user=user, admission_number='A001', full_name='Test Student', course='BSc', department='Computing')
        self.exam = Examination.objects.create(title='Systems', code='SYS101', course='BSc', examination_date=date.today(), start_time=time(9), end_time=time(11), venue='Hall A', status='active')

    def test_only_two_matches_verify_automatically(self):
        self.assertEqual(combine('match', 'match'), 'verified')
        self.assertEqual(combine('match', 'mismatch'), 'manual_review')
        self.assertEqual(combine('unavailable', 'match'), 'manual_review')

    def test_duplicate_attendance_is_not_created(self):
        first, created = record(self.student, self.exam)
        second, created_again = record(self.student, self.exam)
        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Attendance.objects.count(), 1)

    def test_student_cannot_open_admin_page(self):
        self.client.login(username='student', password='test-pass-123')
        response = self.client.get('/students/')
        self.assertEqual(response.status_code, 403)

    def test_registration_waits_for_admin_approval(self):
        response = self.client.post('/register/', {'username':'pending', 'email':'pending@example.com', 'password':'strong-pass-123', 'password_confirm':'strong-pass-123', 'admission_number':'A002', 'full_name':'Pending Student', 'course':'BSc', 'department':'Computing'})
        self.assertEqual(response.status_code, 200)
        pending = get_user_model().objects.get(username='pending')
        self.assertFalse(pending.is_active)
        self.assertFalse(self.client.login(username='pending', password='strong-pass-123'))

    def test_admin_can_approve_account(self):
        admin = get_user_model().objects.create_user(username='admin', password='admin-pass-123', role='admin', is_staff=True)
        pending = get_user_model().objects.create_user(username='pending', password='strong-pass-123', role='student', is_active=False)
        Student.objects.create(user=pending, admission_number='A002', full_name='Pending Student', course='BSc', department='Computing')
        self.client.force_login(admin)
        response = self.client.post(f'/accounts/{pending.pk}/approve/')
        self.assertRedirects(response, '/accounts/pending/')
        pending.refresh_from_db()
        self.assertTrue(pending.is_active)

    def test_dashboard_requires_authentication(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/login/?next=/')

    def test_admin_dashboard_counts_saved_records(self):
        admin = get_user_model().objects.create_user(username='admin-dashboard', password='admin-pass-123', role='admin', is_staff=True)
        self.client.force_login(admin)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['students_count'], 1)
        self.assertEqual(response.context['exams_count'], 1)

    def test_verification_inconclusive_result_creates_human_review_not_verified_attendance(self):
        admin = get_user_model().objects.create_user(username='verification-admin', password='admin-pass-123', role='admin', is_staff=True)
        BiometricProfile.objects.create(student=self.student, fingerprint_reference='SIMULATED-ONLY')
        self.client.force_login(admin)
        response = self.client.post('/biometrics/verify/', {
            'examination': self.exam.pk,
            'admission_number': self.student.admission_number,
            'face_data': '',
        })
        self.assertRedirects(response, '/biometrics/verify/')
        self.assertEqual(VerificationLog.objects.get().overall_result, 'manual_review')
        self.assertEqual(ManualReview.objects.filter(decision='pending').count(), 1)
        self.assertFalse(Attendance.objects.filter(attendance_status=Attendance.Status.PRESENT).exists())

    def test_human_review_clearance_is_audited_and_records_manual_attendance(self):
        admin = get_user_model().objects.create_user(username='review-admin', password='admin-pass-123', role='admin', is_staff=True)
        review = ManualReview.objects.create(student=self.student, examination=self.exam, reason='Test review')
        Attendance.objects.create(student=self.student, examination=self.exam, attendance_status=Attendance.Status.MANUAL, verification_method='DEMO_SAMPLE')
        self.client.force_login(admin)
        response = self.client.post('/reviews/', {
            'review_id': review.pk,
            'decision': 'cleared',
            'notes': 'Identity checked against the approved institutional record.',
        })
        self.assertRedirects(response, '/reviews/')
        review.refresh_from_db()
        self.assertEqual(review.decision, 'cleared')
        attendance = Attendance.objects.get(student=self.student, examination=self.exam)
        self.assertEqual(attendance.verification_method, 'manual_review_approved')
        self.assertTrue(AuditLog.objects.filter(action='manual_review_completed').exists())

    def test_demo_seed_command_requires_explicit_confirmation(self):
        from django.core.management import call_command
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command('seed_demo_data')

    def test_demo_seed_is_synthetic_and_idempotent(self):
        from django.core.management import call_command
        call_command('seed_demo_data', confirm=True)
        self.assertEqual(Student.objects.filter(admission_number__startswith='DEMO-').count(), 5)
        self.assertEqual(Examination.objects.filter(code__startswith='DEMO-').count(), 3)
        self.assertFalse(Attendance.objects.filter(verification_method='DEMO_SAMPLE', attendance_status=Attendance.Status.PRESENT).exists())
        self.assertFalse(BiometricProfile.objects.filter(student__admission_number__startswith='DEMO-').exists())
        call_command('seed_demo_data', confirm=True)
        self.assertEqual(Student.objects.filter(admission_number__startswith='DEMO-').count(), 5)

    def test_superuser_can_load_demo_data_only_when_database_is_empty(self):
        from django.contrib.auth import get_user_model
        Student.objects.all().delete()
        Examination.objects.all().delete()
        admin = get_user_model().objects.create_superuser(username='demo-loader', email='loader@example.invalid', password='admin-pass-123')
        self.client.force_login(admin)
        response = self.client.post('/demo-data/load/')
        self.assertRedirects(response, '/')
        self.assertEqual(Student.objects.filter(admission_number__startswith='DEMO-').count(), 5)
        self.assertEqual(Examination.objects.filter(code__startswith='DEMO-').count(), 3)

    def test_non_superuser_admin_cannot_load_demo_data(self):
        admin = get_user_model().objects.create_user(username='limited-admin', password='admin-pass-123', role='admin')
        self.client.force_login(admin)
        response = self.client.post('/demo-data/load/')
        self.assertEqual(response.status_code, 404)

    def test_facial_templates_are_encrypted_at_rest_and_decryptable(self):
        from integrity.services.face_service import _decrypt_template, encrypt_template
        plain = 'eyJ2ZWN0b3IiOiBbMC4xLCAwLjJdfQ=='
        encrypted = encrypt_template(plain)
        self.assertTrue(encrypted.startswith('fernet:v1:'))
        self.assertNotIn(plain, encrypted)
        self.assertEqual(_decrypt_template(encrypted), plain)

    def test_student_enrollment_requires_separate_face_consent(self):
        self.client.force_login(self.student.user)
        response = self.client.post('/biometrics/enroll/', {
            'student_consent': 'yes',
            'fingerprint_consent': 'yes',
        })
        self.assertRedirects(response, '/biometrics/enroll/')
        self.assertFalse(BiometricProfile.objects.filter(student=self.student).exists())
        self.assertFalse(AuditLog.objects.filter(action='biometric_enrollment').exists())

    def test_enrollment_requires_student_consent(self):
        self.client.force_login(self.student.user)
        response = self.client.post('/biometrics/enroll/', {'fingerprint_consent': 'yes'})
        self.assertRedirects(response, '/biometrics/enroll/')
        self.assertFalse(BiometricProfile.objects.filter(student=self.student).exists())

    def test_fingerprint_enrollment_requires_explicit_enroll_action(self):
        self.client.force_login(self.student.user)
        response = self.client.post('/biometrics/enroll/', {})
        self.assertRedirects(response, '/biometrics/enroll/')
        self.assertFalse(BiometricProfile.objects.filter(student=self.student).exists())

    def test_prototype_biometric_verification_never_auto_records_attendance(self):
        admin = get_user_model().objects.create_user(username='verification-safety-admin', password='admin-pass-123', role='admin')
        BiometricProfile.objects.create(student=self.student, fingerprint_reference='SIMULATION-NOT-A-BIOMETRIC')
        self.client.force_login(admin)
        response = self.client.post('/biometrics/verify/', {
            'examination': self.exam.pk,
            'admission_number': self.student.admission_number,
            'face_data': '',
        })
        self.assertRedirects(response, '/biometrics/verify/')
        log = VerificationLog.objects.get()
        self.assertEqual(log.fingerprint_result, 'unavailable')
        self.assertEqual(log.overall_result, 'manual_review')
        self.assertFalse(Attendance.objects.filter(student=self.student, examination=self.exam, attendance_status=Attendance.Status.PRESENT).exists())

    def test_even_a_future_verified_adapter_result_requires_human_review(self):
        from unittest.mock import patch
        admin = get_user_model().objects.create_user(username='future-adapter-admin', password='admin-pass-123', role='admin')
        BiometricProfile.objects.create(student=self.student, fingerprint_reference='SIMULATION-NOT-A-BIOMETRIC')
        self.client.force_login(admin)
        mocked_result = {
            'fingerprint_result': 'match',
            'facial_result': 'match',
            'overall_result': 'verified',
        }
        with patch('integrity.services.verification_service.verify', return_value=mocked_result):
            response = self.client.post('/biometrics/verify/', {
                'examination': self.exam.pk,
                'admission_number': self.student.admission_number,
                'face_data': '',
            })
        self.assertRedirects(response, '/biometrics/verify/')
        self.assertEqual(VerificationLog.objects.get().overall_result, 'verified')
        self.assertTrue(ManualReview.objects.filter(student=self.student, examination=self.exam, decision='pending').exists())
        self.assertFalse(Attendance.objects.filter(
            student=self.student,
            examination=self.exam,
            attendance_status=Attendance.Status.PRESENT,
        ).exists())

    def test_admin_enrollment_requires_face_capture_even_when_consents_are_given(self):
        admin = get_user_model().objects.create_user(username='biometric-admin', password='admin-pass-123', role='admin')
        self.client.force_login(admin)
        response = self.client.post('/biometrics/enroll/', {
            'student_id': self.student.pk,
            'student_consent': 'yes',
            'fingerprint_consent': 'yes',
            'face_consent': 'yes',
        })
        self.assertRedirects(response, '/biometrics/enroll/')
        self.assertFalse(BiometricProfile.objects.filter(student=self.student).exists())
        self.assertFalse(AuditLog.objects.filter(action='biometric_enrollment').exists())
