from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connections, transaction
from django.db.models import Q

from integrity.models import (
    Attendance,
    AuditLog,
    Examination,
    ExaminationRegistration,
    IdentityVerification,
    IncidentAuditEvent,
    IncidentCase,
    Invigilator,
    ManualReview,
    Student,
    User,
)


class Command(BaseCommand):
    help = (
        "Import the previous Vercel SQLite records into an empty managed "
        "database without importing seeded demo or retired biometric data."
    )

    source_alias = "legacy_sqlite"
    target_alias = "default"

    def handle(self, *args, **options):
        if self.source_alias not in connections:
            self.stdout.write("No legacy SQLite source is configured; import skipped.")
            return

        if User.objects.using(self.target_alias).exists():
            self.stdout.write(
                "The managed database already contains users; legacy import skipped "
                "to prevent duplicate or overwritten records."
            )
            return

        source_tables = connections[self.source_alias].introspection.table_names()
        if User._meta.db_table not in source_tables:
            self.stdout.write("The legacy SQLite file has no application user table; import skipped.")
            return

        legacy = self.source_alias
        demo_students = Student.objects.using(legacy).filter(
            Q(admission_number__istartswith="DEMO-")
            | Q(full_name__in=[
                "Alex Sample",
                "Jordan Example",
                "Taylor Synthetic",
                "Casey Placeholder",
                "Riley Demonstration",
            ])
        )
        demo_student_ids = list(demo_students.values_list("pk", flat=True))
        demo_user_ids = list(demo_students.values_list("user_id", flat=True))
        student_ids = list(
            Student.objects.using(legacy).exclude(pk__in=demo_student_ids)
            .values_list("pk", flat=True)
        )

        demo_examinations = Examination.objects.using(legacy).filter(
            Q(code__istartswith="DEMO-")
            | Q(title__istartswith="DEMO")
            | Q(venue__istartswith="DEMO")
        )
        demo_examination_ids = list(demo_examinations.values_list("pk", flat=True))
        examination_ids = list(
            Examination.objects.using(legacy).exclude(pk__in=demo_examination_ids)
            .values_list("pk", flat=True)
        )

        user_ids = list(
            User.objects.using(legacy)
            .exclude(pk__in=demo_user_ids)
            .exclude(username__istartswith="demo-student-")
            .values_list("pk", flat=True)
        )
        invigilator_ids = list(
            Invigilator.objects.using(legacy)
            .filter(user_id__in=user_ids)
            .values_list("pk", flat=True)
        )
        case_ids = list(
            IncidentCase.objects.using(legacy)
            .filter(
                student_id__in=student_ids,
                examination_id__in=examination_ids,
                created_by_id__in=user_ids,
                assigned_invigilator_id__in=user_ids,
            )
            .filter(Q(board_reviewer_id__isnull=True) | Q(board_reviewer_id__in=user_ids))
            .values_list("pk", flat=True)
        )

        copied = {}
        with transaction.atomic(using=self.target_alias):
            copied["users"] = self._copy_rows(
                User.objects.using(legacy).filter(pk__in=user_ids), User
            )
            copied["invigilators"] = self._copy_rows(
                Invigilator.objects.using(legacy).filter(
                    pk__in=invigilator_ids, user_id__in=user_ids
                ),
                Invigilator,
            )
            copied["students"] = self._copy_rows(
                Student.objects.using(legacy).filter(pk__in=student_ids, user_id__in=user_ids),
                Student,
            )
            copied["examinations"] = self._copy_rows(
                Examination.objects.using(legacy).filter(pk__in=examination_ids),
                Examination,
            )
            copied["registrations"] = self._copy_rows(
                ExaminationRegistration.objects.using(legacy).filter(
                    student_id__in=student_ids, examination_id__in=examination_ids
                ),
                ExaminationRegistration,
            )

            attendance_rows = Attendance.objects.using(legacy).filter(
                student_id__in=student_ids,
                examination_id__in=examination_ids,
            ).exclude(verification_method__iexact="DEMO_SAMPLE")
            copied["attendance"] = self._copy_rows(
                attendance_rows, Attendance, normalize_legacy_attendance=True
            )

            copied["identity_checks"] = self._copy_rows(
                IdentityVerification.objects.using(legacy).filter(
                    student_id__in=student_ids,
                    examination_id__in=examination_ids,
                    checked_by_id__in=user_ids,
                ),
                IdentityVerification,
            )
            copied["manual_reviews"] = self._copy_rows(
                ManualReview.objects.using(legacy).filter(
                    student_id__in=student_ids,
                    examination_id__in=examination_ids,
                ).filter(
                    Q(invigilator_id__isnull=True) | Q(invigilator_id__in=invigilator_ids)
                ).exclude(reason__icontains="DEMO SAMPLE ONLY"),
                ManualReview,
            )
            copied["incident_cases"] = self._copy_rows(
                IncidentCase.objects.using(legacy).filter(pk__in=case_ids),
                IncidentCase,
            )
            copied["incident_audit_events"] = self._copy_rows(
                IncidentAuditEvent.objects.using(legacy).filter(
                    case_id__in=case_ids, actor_id__in=user_ids
                ),
                IncidentAuditEvent,
            )

            audit_rows = AuditLog.objects.using(legacy).filter(
                Q(user_id__isnull=True) | Q(user_id__in=user_ids)
            ).exclude(
                Q(action__icontains="biometric")
                | Q(action__iexact="verification_referred")
                | Q(description__icontains="DEMO-")
                | Q(description__icontains="DEMO SAMPLE ONLY")
                | Q(description__icontains="prototype biometric")
                | Q(description__icontains="biometric prototype")
                | Q(description__icontains="facial template")
            )
            copied["audit_logs"] = self._copy_rows(audit_rows, AuditLog)

            self._copy_examination_invigilator_links(examination_ids, invigilator_ids)
            self._restore_legacy_attendance_reviews()

            reset_models = [
                User, Invigilator, Student, Examination, ExaminationRegistration,
                Attendance, IdentityVerification, ManualReview, IncidentCase,
                IncidentAuditEvent, AuditLog, Examination.invigilators.through,
            ]
            statements = connections[self.target_alias].ops.sequence_reset_sql(
                no_style(), reset_models
            )
            with connections[self.target_alias].cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)

        summary = ", ".join(f"{name}={count}" for name, count in copied.items())
        self.stdout.write(self.style.SUCCESS(f"Legacy SQLite import completed: {summary}"))
        self.stdout.write(
            "Retired biometric profiles/logs and recognisable demo records were not imported."
        )

    def _copy_rows(self, queryset, model, normalize_legacy_attendance=False):
        fields = [field.attname for field in model._meta.concrete_fields]
        rows = list(queryset.values(*fields))
        if not rows:
            return 0

        if normalize_legacy_attendance and model is Attendance:
            for row in rows:
                if str(row["verification_method"]).lower() == "biometric":
                    row["attendance_status"] = Attendance.Status.MANUAL
                    row["verification_method"] = "legacy_unverified_review_required"

        instances = [model(**row) for row in rows]
        model.objects.using(self.target_alias).bulk_create(instances, batch_size=500)

        # bulk_create honours auto_now fields; restore original timestamps and
        # every source field through QuerySet.update so historical evidence stays
        # historically dated and model save hooks are not invoked.
        pk_name = model._meta.pk.attname
        for row in rows:
            pk = row[pk_name]
            values = {key: value for key, value in row.items() if key != pk_name}
            model.objects.using(self.target_alias).filter(pk=pk).update(**values)
        return len(rows)

    def _copy_examination_invigilator_links(self, examination_ids, invigilator_ids):
        through = Examination.invigilators.through
        rows = list(
            through.objects.using(self.source_alias)
            .filter(
                examination_id__in=examination_ids,
                invigilator_id__in=invigilator_ids,
            )
            .values("id", "examination_id", "invigilator_id")
        )
        if rows:
            through.objects.using(self.target_alias).bulk_create(
                [through(**row) for row in rows], batch_size=500
            )
            for row in rows:
                through.objects.using(self.target_alias).filter(pk=row["id"]).update(
                    examination_id=row["examination_id"],
                    invigilator_id=row["invigilator_id"],
                )

    def _restore_legacy_attendance_reviews(self):
        legacy_rows = Attendance.objects.using(self.target_alias).filter(
            verification_method="legacy_unverified_review_required"
        )
        for row in legacy_rows.iterator():
            ManualReview.objects.using(self.target_alias).get_or_create(
                student_id=row.student_id,
                examination_id=row.examination_id,
                decision="pending",
                defaults={
                    "reason": (
                        "A previous prototype recorded attendance using an "
                        "unverified biometric workflow. A staff member must review "
                        "the original attendance evidence before this can be cleared."
                    )
                },
            )
