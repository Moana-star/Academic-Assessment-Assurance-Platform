from datetime import date, time

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class RemoveSeededDemoRecordsMigrationTests(TransactionTestCase):
    migrate_from = [("integrity", "0005_identityverification")]
    migrate_to = [("integrity", "0006_remove_seeded_demo_records")]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        executor = MigrationExecutor(connection)
        executor.migrate(cls.migrate_from)
        old_apps = executor.loader.project_state(cls.migrate_from).apps

        User = old_apps.get_model("integrity", "User")
        Student = old_apps.get_model("integrity", "Student")
        Examination = old_apps.get_model("integrity", "Examination")
        Attendance = old_apps.get_model("integrity", "Attendance")
        ManualReview = old_apps.get_model("integrity", "ManualReview")
        AuditLog = old_apps.get_model("integrity", "AuditLog")
        BiometricProfile = old_apps.get_model("integrity", "BiometricProfile")
        VerificationLog = old_apps.get_model("integrity", "VerificationLog")

        demo_user = User.objects.create(
            username="demo-student-001", password="!", role="student", is_active=False
        )
        demo_student = Student.objects.create(
            user=demo_user, admission_number="DEMO-001", full_name="Alex Sample",
            course="BSc Computer Science", department="Computing",
        )
        demo_exam = Examination.objects.create(
            title="DEMO — Database Systems", code="DEMO-COMP204", course="BSc",
            examination_date=date(2026, 11, 22), start_time=time(9),
            end_time=time(11), venue="DEMO Lab 2", status="active",
        )
        Attendance.objects.create(
            student=demo_student, examination=demo_exam,
            attendance_status="manual", verification_method="DEMO_SAMPLE",
        )
        ManualReview.objects.create(
            student=demo_student, examination=demo_exam,
            reason="DEMO SAMPLE ONLY — synthetic case.", decision="pending",
        )
        AuditLog.objects.create(
            user=demo_user, action="biometric_enrollment",
            description="Biometric prototype enrollment for DEMO-001 in DEMO-COMP204.",
        )

        real_user = User.objects.create(
            username="mercy-real", password="!", role="student", is_active=True
        )
        real_student = Student.objects.create(
            user=real_user, admission_number="IN13/00091/23",
            full_name="Mercy Kerubo Nyangau", course="Computer science",
            department="IT",
        )
        real_exam = Examination.objects.create(
            title="SYSTEM ANALYSIS AND DESIGN", code="COMP212", course="Computer science",
            examination_date=date(2026, 11, 24), start_time=time(9),
            end_time=time(11), venue="C22", status="active",
        )
        legacy_attendance = Attendance.objects.create(
            student=real_student, examination=real_exam,
            attendance_status="present", verification_method="biometric",
        )
        BiometricProfile.objects.create(
            student=real_student, fingerprint_reference="SIMULATION-NOT-A-BIOMETRIC",
            facial_template="legacy prototype template",
        )
        VerificationLog.objects.create(
            student=real_student, examination=real_exam,
            fingerprint_result="unavailable", facial_result="inconclusive",
            overall_result="referred",
        )
        AuditLog.objects.create(
            user=real_user, action="attendance_imported",
            description="Institutional attendance record for COMP212.",
        )

        executor = MigrationExecutor(connection)
        executor.migrate(cls.migrate_to)
        cls.apps = executor.loader.project_state(cls.migrate_to).apps

    @classmethod
    def tearDownClass(cls):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDownClass()

    def test_cleanup_removes_demo_data_preserves_real_records_and_quarantines_biometric_attendance(self):
        Student = self.apps.get_model("integrity", "Student")
        Examination = self.apps.get_model("integrity", "Examination")
        ManualReview = self.apps.get_model("integrity", "ManualReview")
        AuditLog = self.apps.get_model("integrity", "AuditLog")
        Attendance = self.apps.get_model("integrity", "Attendance")
        BiometricProfile = self.apps.get_model("integrity", "BiometricProfile")
        VerificationLog = self.apps.get_model("integrity", "VerificationLog")

        self.assertFalse(Student.objects.filter(admission_number="DEMO-001").exists())
        self.assertFalse(Examination.objects.filter(code="DEMO-COMP204").exists())
        self.assertFalse(ManualReview.objects.filter(reason__icontains="DEMO SAMPLE ONLY").exists())
        self.assertFalse(AuditLog.objects.filter(description__icontains="DEMO-").exists())
        self.assertFalse(AuditLog.objects.filter(action__icontains="biometric").exists())

        self.assertTrue(Student.objects.filter(admission_number="IN13/00091/23").exists())
        self.assertTrue(Examination.objects.filter(code="COMP212").exists())
        self.assertTrue(AuditLog.objects.filter(description__icontains="COMP212").exists())

        student = Student.objects.get(admission_number="IN13/00091/23")
        examination = Examination.objects.get(code="COMP212")
        attendance = Attendance.objects.get(student=student, examination=examination)
        self.assertEqual(attendance.attendance_status, "manual")
        self.assertEqual(attendance.verification_method, "legacy_unverified_review_required")
        self.assertTrue(ManualReview.objects.filter(
            student=student, examination=examination, decision="pending"
        ).exists())

        self.assertEqual(BiometricProfile.objects.count(), 0)
        self.assertEqual(VerificationLog.objects.count(), 0)
