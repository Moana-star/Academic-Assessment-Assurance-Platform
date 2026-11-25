from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from integrity.forms import ExaminationForm
from integrity.models import AuditLog, Examination, ExaminationRegistration, Invigilator, Student

User = get_user_model()


class AcademicOperationsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="operations-admin", password="Secure-test-pass-123!",
            role="admin", is_staff=True,
        )
        self.student_user = User.objects.create_user(
            username="candidate-one", password="Secure-test-pass-123!",
            role="student",
        )
        self.student = Student.objects.create(
            user=self.student_user, admission_number="OPS/001",
            full_name="Candidate One", course="Computer Science",
            department="Computing",
        )
        self.exam = Examination.objects.create(
            title="Systems Analysis", code="OPS212", course="Computer Science",
            examination_date=date.today(), start_time=time(9), end_time=time(12),
            venue="Room C22", status=Examination.Status.UPCOMING,
        )
        self.client.force_login(self.admin)

    def test_admin_can_register_candidate_for_specific_examination(self):
        response = self.client.post(
            reverse("examination_manage", args=[self.exam.pk]),
            {"action": "register_student", "student_id": self.student.pk},
        )
        self.assertRedirects(response, reverse("examination_manage", args=[self.exam.pk]))
        self.assertTrue(
            ExaminationRegistration.objects.filter(
                student=self.student, examination=self.exam
            ).exists()
        )
        self.assertTrue(AuditLog.objects.filter(action="examination_student_registered").exists())

    def test_registration_action_is_idempotent(self):
        payload = {"action": "register_student", "student_id": self.student.pk}
        self.client.post(reverse("examination_manage", args=[self.exam.pk]), payload)
        self.client.post(reverse("examination_manage", args=[self.exam.pk]), payload)
        self.assertEqual(ExaminationRegistration.objects.filter(examination=self.exam).count(), 1)

    def test_admin_can_assign_only_an_approved_invigilator(self):
        staff_user = User.objects.create_user(
            username="approved-staff", password="Secure-test-pass-123!",
            role="invigilator", is_active=True,
        )
        staff = Invigilator.objects.create(
            user=staff_user, staff_number="STAFF-OPS-1",
            full_name="Approved Staff", department="Computing",
        )
        response = self.client.post(
            reverse("examination_manage", args=[self.exam.pk]),
            {"action": "assign_invigilator", "invigilator_id": staff.pk},
        )
        self.assertRedirects(response, reverse("examination_manage", args=[self.exam.pk]))
        self.assertTrue(self.exam.invigilators.filter(pk=staff.pk).exists())
        self.assertTrue(AuditLog.objects.filter(action="examination_invigilator_assigned").exists())

    def test_pending_invigilator_cannot_be_assigned(self):
        staff_user = User.objects.create_user(
            username="pending-staff", password="Secure-test-pass-123!",
            role="invigilator", is_active=False,
        )
        staff = Invigilator.objects.create(
            user=staff_user, staff_number="STAFF-OPS-2",
            full_name="Pending Staff", department="Computing",
        )
        self.client.post(
            reverse("examination_manage", args=[self.exam.pk]),
            {"action": "assign_invigilator", "invigilator_id": staff.pk},
        )
        self.assertFalse(self.exam.invigilators.filter(pk=staff.pk).exists())

    def test_admin_can_update_examination_status_and_audit_it(self):
        response = self.client.post(
            reverse("examination_manage", args=[self.exam.pk]),
            {"action": "update_status", "status": Examination.Status.ACTIVE},
        )
        self.assertRedirects(response, reverse("examination_manage", args=[self.exam.pk]))
        self.exam.refresh_from_db()
        self.assertEqual(self.exam.status, Examination.Status.ACTIVE)
        self.assertTrue(AuditLog.objects.filter(action="examination_status_updated").exists())

    def test_past_examination_cannot_be_marked_active(self):
        self.exam.examination_date = date.today() - timedelta(days=1)
        self.exam.save(update_fields=["examination_date"])
        self.client.post(
            reverse("examination_manage", args=[self.exam.pk]),
            {"action": "update_status", "status": Examination.Status.ACTIVE},
        )
        self.exam.refresh_from_db()
        self.assertEqual(self.exam.status, Examination.Status.UPCOMING)

    def test_examination_form_rejects_end_time_before_start_time(self):
        form = ExaminationForm(data={
            "title": "Invalid schedule", "code": "BAD212",
            "course": "Computer Science", "examination_date": date.today().isoformat(),
            "start_time": "12:00", "end_time": "09:00",
            "venue": "Room A", "status": Examination.Status.UPCOMING,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("end_time", form.errors)

    def test_invigilator_management_creates_inactive_profile_for_approval(self):
        response = self.client.post(reverse("invigilator_add"), {
            "username": "new-staff", "email": "staff@example.test",
            "temporary_password": "Very-Strong-Test-Password-123!",
            "staff_number": "STAFF-NEW-1", "full_name": "New Staff",
            "department": "Computing",
        })
        self.assertRedirects(response, reverse("invigilators"))
        staff_user = User.objects.get(username="new-staff")
        self.assertFalse(staff_user.is_active)
        self.assertEqual(staff_user.role, User.Roles.INVIGILATOR)
        self.assertEqual(staff_user.invigilator_profile.staff_number, "STAFF-NEW-1")
