from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from integrity.models import Attendance, Examination, ExaminationRegistration, ManualReview, Student


class Command(BaseCommand):
    help = "Create clearly labelled synthetic records for a supervised platform demonstration."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirm that synthetic demonstration records may be added to the configured database.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["confirm"]:
            raise CommandError(
                "No records were created. Re-run with --confirm after checking which database is configured."
            )

        User = get_user_model()
        today = timezone.localdate()
        students_data = [
            ("DEMO-001", "Alex Sample", "BSc Computer Science", "Computing"),
            ("DEMO-002", "Jordan Example", "BSc Information Technology", "Computing"),
            ("DEMO-003", "Taylor Synthetic", "BSc Software Engineering", "Computing"),
            ("DEMO-004", "Casey Placeholder", "BSc Data Science", "Computing"),
            ("DEMO-005", "Riley Demonstration", "BSc Cybersecurity", "Computing"),
        ]
        students = []
        for admission, full_name, course, department in students_data:
            username = f"demo-student-{admission[-3:]}"
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.invalid",
                    "role": User.Roles.STUDENT,
                    "is_active": False,
                },
            )
            if user.has_usable_password() or user.is_active:
                user.set_unusable_password()
                user.is_active = False
                user.save(update_fields=["password", "is_active"])
            student, _ = Student.objects.get_or_create(
                admission_number=admission,
                defaults={
                    "user": user,
                    "full_name": full_name,
                    "course": course,
                    "department": department,
                },
            )
            students.append(student)

        exam_specs = [
            {
                "title": "DEMO — Introduction to Programming",
                "code": "DEMO-COMP101",
                "course": "BSc Computer Science",
                "examination_date": today + timedelta(days=2),
                "start_time": "09:00",
                "end_time": "11:00",
                "venue": "DEMO Hall A",
                "status": Examination.Status.UPCOMING,
            },
            {
                "title": "DEMO — Database Systems",
                "code": "DEMO-COMP204",
                "course": "BSc Computer Science",
                "examination_date": today,
                "start_time": "14:00",
                "end_time": "16:00",
                "venue": "DEMO Lab 2",
                "status": Examination.Status.ACTIVE,
            },
            {
                "title": "DEMO — Software Engineering",
                "code": "DEMO-COMP305",
                "course": "BSc Computer Science",
                "examination_date": today - timedelta(days=2),
                "start_time": "09:00",
                "end_time": "12:00",
                "venue": "DEMO Hall B",
                "status": Examination.Status.COMPLETED,
            },
        ]
        exams = []
        for spec in exam_specs:
            exam, _ = Examination.objects.get_or_create(code=spec["code"], defaults=spec)
            exams.append(exam)

        for student in students:
            for exam in exams[:2]:
                ExaminationRegistration.objects.get_or_create(student=student, examination=exam)

        active_exam = exams[1]
        sample_student = students[0]
        Attendance.objects.get_or_create(
            student=sample_student,
            examination=active_exam,
            defaults={
                "attendance_status": Attendance.Status.MANUAL,
                "verification_method": "DEMO_SAMPLE",
            },
        )
        ManualReview.objects.get_or_create(
            student=sample_student,
            examination=active_exam,
            decision="pending",
            defaults={
                "reason": "DEMO SAMPLE ONLY — synthetic case created to demonstrate the human-review queue. No biometric decision was performed.",
            },
        )

        self.stdout.write(self.style.SUCCESS(
            "Synthetic demonstration dataset is ready: 5 students, 3 examinations, registrations, "
            "1 manual-review attendance sample, and 1 pending human-review case. "
            "No biometric templates, photographs, or verified attendance were fabricated."
        ))
