from datetime import date, time
from django.contrib.auth import get_user_model
from django.test import TestCase
from integrity.models import Attendance, Examination, Student
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
